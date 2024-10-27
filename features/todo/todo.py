import firebase_admin
import features.todo.util_todo as util
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta, date
from discord.ext import commands

# firebase init
cred = credentials.Certificate("features/todo/todo-app-key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def setup(bot):
   #get user reference from firestore
   def get_user_ref(ctx):
      user_id = str(ctx.author.id)
      return (
         db.collection('users')
            .document(user_id)
            .collection('tasks')
      )

   #get user tasks from firestore
   async def get_user_tasks(ctx):
      tasks_ref = get_user_ref(ctx)
      docs = tasks_ref.stream()
      tasks = {}
      for doc in docs:
         tasks[doc.id] = doc.to_dict()
      return tasks_ref, tasks

   @bot.command(name='add')
   async def add_task(ctx, task: str, deadline: str):
      tasks_ref = get_user_ref(ctx)
      
      # Check if the date is valid
      is_valid, result = util.is_valid_date(deadline)
      if not is_valid:
         await ctx.send(result)
         return
      
      # Result is a valid date
      deadline_date = result

      # Initialize the new task
      new_task = {
         "task": task,
         "completed": False,
         "overdue": False,
         "deadline": deadline_date.isoformat() if deadline_date else None,
         "created_at": datetime.now().isoformat()
      }
      
      # Add the new task to the database
      tasks_ref.add(new_task)
      await ctx.send(f'Đã thêm công việc: {task}')

   @bot.command(name='list')
   async def list_tasks(ctx):
      tasks_ref, tasks = await get_user_tasks(ctx)
      if not tasks:
         await ctx.send('Danh sách công việc của bạn trống.')
         return

      # check overdue tasks and update the database
      await check_overdue_tasks(tasks_ref, tasks)

      # get the updated tasks
      tasks_ref, tasks = await get_user_tasks(ctx)
      
      # sort the tasks
      sorted_tasks = util.sort_tasks(tasks)
      
      # format the tasks
      task_list = []
      for i, task_info in enumerate(sorted_tasks, 1):
         value = task_info['data']
         # format the status of the task
         if value['completed']:
            status = '✓'
         elif value.get('overdue', False):
            status = 'O'
         else:
            status = '✗'
            
         deadline = ""
         if value['deadline']:
            deadline_date = datetime.fromisoformat(value['deadline']).date()  # convert deadline to date
            deadline = f"Exp: {deadline_date.strftime('%d/%m/%Y')}"
            # format the deadline to show the days left
            if not value['completed'] and not value.get('overdue', False):
               days_left = task_info['days_until_deadline']
               if days_left == 0:
                  deadline += " (Hôm nay)"
               elif days_left == 1:
                  deadline += " (Ngày mai)"
               else:
                  deadline += f" (Còn {days_left} ngày)"

         task_list.append(f"{i}. [{status}] - {value['task']} - {deadline}".strip())
      
      # send the formatted list to the user
      formatted_list = '\n'.join(task_list)
      await ctx.send(f'Danh sách công việc của bạn:\n{formatted_list}')

   @bot.command(name='edit')
   async def edit_task(ctx, index: int, new_task_description: str):
      tasks_ref, tasks = await get_user_tasks(ctx)
      # check index is valid [1, len(tasks)]
      if tasks and 0 < index <= len(tasks):

         task_id = list(tasks.keys())[index-1] # get selected task id
         old_task = tasks[task_id]['task'] # get old task description

         # update the task description
         tasks_ref.document(task_id).update({'task': new_task_description})

         await ctx.send(f'Đã sửa công việc:\nCũ: {old_task}\nMới: {new_task_description}')
      else:
         await ctx.send('Không tìm thấy công việc với số thứ tự này.')

   @bot.command(name='complete')
   async def complete_task(ctx, index: int, status: int):
      tasks_ref, tasks = await get_user_tasks(ctx)
      # check status is valid [0, 1]
      if not (status == 0 or status == 1):
         await ctx.send('Trạng thái không hợp lệ. Vui lòng sử dụng 0 (chưa hoàn thành) hoặc 1 (đã hoàn thành).')
         return
      
      if tasks and 0 < index <= len(tasks):
         # get selected task id
         task_id = list(tasks.keys())[index-1] 

         # update the task status
         updates = {
            'completed': bool(status),
            'overdue': False
         }

         # update status in the database
         tasks_ref.document(task_id).update(updates)
         status_text = "hoàn thành" if status == 1 else "chưa hoàn thành"

         await ctx.send(f'Đã đánh dấu công việc {index} là {status_text}.')
      else:
         await ctx.send('Không tìm thấy công việc với số thứ tự này.')

   @bot.command(name='delete')
   async def delete_task(ctx, index: int):
      tasks_ref, tasks = await get_user_tasks(ctx)
      if tasks and 0 < index <= len(tasks):
         # get selected task id
         task_id = list(tasks.keys())[index-1]

         # get the task to be deleted
         deleted_task = tasks[task_id] 

         # delete the task from the database
         tasks_ref.document(task_id).delete()

         await ctx.send(f'Đã xóa công việc: {deleted_task["task"]}')
      else:
         await ctx.send('Không tìm thấy công việc với số thứ tự này.')

   @bot.command(name='deadline')
   async def set_deadline(ctx, index: int, deadline: str):
      tasks_ref, tasks = await get_user_tasks(ctx)
      if tasks and 0 < index <= len(tasks):
         # Check the date is valid, if not send an error message
         is_valid, result = util.is_valid_date(deadline)
         if not is_valid:
            await ctx.send(result)
            return
         
         # get selected task id
         task_id = list(tasks.keys())[index-1]

         # update the deadline in the database
         tasks_ref.document(task_id).update({
            'deadline': result.isoformat(),
            'overdue': False
         })
         await ctx.send(f'Đã đặt hạn cho công việc {index}: {deadline}')
      else:
         await ctx.send('Không tìm thấy công việc với số thứ tự này.')

   @bot.command(name='list_w')
   async def list_this_week_tasks(ctx):
      # get user tasks and check tasks is empty
      tasks_ref, tasks = await get_user_tasks(ctx)
      if not tasks:
         await ctx.send('Danh sách công việc của bạn trống.')
         return

      # check overdue tasks and update the database
      await check_overdue_tasks(tasks_ref, tasks)
      tasks_ref, tasks = await get_user_tasks(ctx)

      # get the start and end of the week
      today = date.today()
      start_of_week = today - timedelta(days=today.weekday())
      end_of_week = start_of_week + timedelta(days=6)
      
      task_list = []
      task_count = 0
      for task_info in util.sort_tasks(tasks):
         value = task_info['data']
         print(value)
         # skip completed tasks
         if value['completed']:
            continue
         
         # check if the task has a deadline and the deadline is within the week
         if value['deadline']:
            deadline_date = datetime.fromisoformat(value['deadline']).date()
            if start_of_week <= deadline_date <= end_of_week:
               deadline = f"Exp: {deadline_date.strftime('%d/%m/%Y')}"
               status = 'O' if value.get('overdue', False) else '✗'
               task_count += 1
               task_list.append(f"{task_count}. [{status}] - {value['task']} - {deadline}")

      if task_list:
         formatted_list = '\n'.join(task_list)
         await ctx.send(f'Danh sách công việc chưa hoàn thành trong tuần này:\n{formatted_list}')
      else:
         await ctx.send('Không có công việc chưa hoàn thành trong tuần này.')

   @bot.command(name='list_nw')
   async def list_next_week_tasks(ctx):
      tasks_ref, tasks = await get_user_tasks(ctx)
      if not tasks:
         await ctx.send('Danh sách công việc của bạn trống.')
         return

      # check overdue tasks and update the database
      await check_overdue_tasks(tasks_ref, tasks)
      tasks_ref, tasks = await get_user_tasks(ctx)

      # get the start and end of the next week
      today = date.today()
      start_of_next_week = today + timedelta(days=(7 - today.weekday()))
      end_of_next_week = start_of_next_week + timedelta(days=6)
      
      task_list = []
      task_count = 0
      for task_info in util.sort_tasks(tasks):
         # skip completed tasks
         value = task_info['data']
         if value['completed']:
            continue
         
         # check if the task has a deadline and the deadline is within the next week
         if value['deadline']:
            deadline_date = datetime.fromisoformat(value['deadline']).date()
            if start_of_next_week <= deadline_date <= end_of_next_week:
               deadline = f"Exp: {deadline_date.strftime('%d/%m/%Y')}"
               status = 'O' if value.get('overdue', False) else '✗'
               task_count += 1
               task_list.append(f"{task_count}. [{status}] - {value['task']} - {deadline}")

      # send the formatted list to the user
      if task_list:
         formatted_list = '\n'.join(task_list)
         legend = "\nChú thích:\n[✗] - Chưa hoàn thành\n[O] - Quá hạn"
         await ctx.send(f'Danh sách công việc chưa hoàn thành trong tuần tới:\n{formatted_list}{legend}')
      else:
         await ctx.send('Không có công việc chưa hoàn thành trong tuần tới.')

   @bot.command(name='clear')
   async def clear_tasks(ctx):
      # Get user tasks reference
      tasks_ref = get_user_ref(ctx)
      tasks = tasks_ref.stream()

      # Delete all tasks
      for task in tasks:
         task.reference.delete()

      await ctx.send("Đã xóa tất cả công việc.")

   @bot.command(name='todo')
   async def help_command(ctx):
      try:
         with open('features/todo/todo_help.txt', 'r', encoding='utf-8') as file:
            help_content = file.read()
         await ctx.send(f'```{help_content}```') 
      except Exception as e:
         await ctx.send(f"Có lỗi xảy ra: {str(e)}")

   async def check_overdue_tasks(tasks_ref, tasks):
      # exit if tasks is empty
      if not tasks:
         return

      current_date = date.today()
      batch = db.batch()

      # Check for overdue tasks
      for doc_id, value in tasks.items():
         if not value['completed'] and value['deadline']:
            deadline_date = datetime.fromisoformat(value['deadline']).date()
            if deadline_date < current_date and not value.get('overdue', False):
               doc_ref = tasks_ref.document(doc_id)
               batch.update(doc_ref, {'overdue': True})

      batch.commit()