import firebase_admin, asyncio
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta, date
from discord.ext import commands

import util.util_todo as util

class TodoCog(commands.Cog,name="Todo"):
   def __init__(self, bot):
      self.bot = bot
      # Initialize Firebase
      cred = credentials.Certificate("features/todo/todo-app-key.json")
      if not firebase_admin._apps:
         firebase_admin.initialize_app(cred)
      self.db = firestore.client()

   def get_user_ref(self, ctx):
      # Get a reference to a user's tasks collection in Firebase.
      user_id = str(ctx.author.id)
      return (
         self.db.collection('users')
            .document(user_id)
            .collection('tasks')
      )

   async def get_user_tasks(self, ctx):
      # Retrieve all tasks for a user from Firebase.
      tasks_ref = self.get_user_ref(ctx)
      docs = tasks_ref.stream()
      tasks = {}
      for doc in docs:
         tasks[doc.id] = doc.to_dict()
      return tasks_ref, tasks

   @commands.command(name='add')
   async def add_task(self, ctx, task: str, deadline: str):
      tasks_ref = self.get_user_ref(ctx)
      
      # Validate the deadline date format
      is_valid, result = util.is_valid_date(deadline)
      if not is_valid:
         await ctx.send(result)
         return
      
      # Create new task object with default values
      new_task = {
         "task": task,
         "completed": False,
         "overdue": False,
         "deadline": result.isoformat() if result else None,
         "created_at": datetime.now().isoformat()
      }
      
      tasks_ref.add(new_task)
      await ctx.send(f'Đã thêm công việc: {task}')

   @commands.command(name='list')
   async def list_tasks(self, ctx):
      tasks_ref, tasks = await self.get_user_tasks(ctx)
      if not tasks:
         await ctx.send('Danh sách công việc của bạn trống.')
         return

      # Update overdue status for all tasks
      await self.check_overdue_tasks(tasks_ref, tasks)

      # Refresh tasks after updating overdue status
      tasks_ref, tasks = await self.get_user_tasks(ctx)
      
      # Sort tasks
      sorted_tasks = util.sort_tasks(tasks)
      
      # Format each task with status and deadline information
      task_list = []
      for i, task_info in enumerate(sorted_tasks, 1):
         value = task_info['data']
         # Determine task status icon
         if value['completed']:
            status = '✓'
         elif value.get('overdue', False):
            status = 'O'
         else:
            status = '✗'
            
         # Format deadline information
         deadline = ""
         if value['deadline']:
            deadline_date = datetime.fromisoformat(value['deadline']).date()
            deadline = f"Exp: {deadline_date.strftime('%d/%m/%Y')}"
            # Add remaining days information for incomplete tasks
            if not value['completed'] and not value.get('overdue', False):
               days_left = task_info['days_until_deadline']
               if days_left == 0:
                  deadline += " (Hôm nay)"
               elif days_left == 1:
                  deadline += " (Ngày mai)"
               else:
                  deadline += f" (Còn {days_left} ngày)"

         task_list.append(f"{i}. [{status}] - {value['task']} - {deadline}".strip())
      
      formatted_list = '\n'.join(task_list)
      await ctx.send(f'Danh sách công việc của bạn:\n{formatted_list}')

   @commands.command(name='edit')
   async def edit_task(self, ctx, index: int, new_task_description: str):
      tasks_ref, tasks = await self.get_user_tasks(ctx)

      # Check if the task index is valid
      if tasks and 0 < index <= len(tasks):
         task_id = list(tasks.keys())[index-1]

         # Save the old task description for the response message
         old_task = tasks[task_id]['task']

         tasks_ref.document(task_id).update({'task': new_task_description})
         await ctx.send(f'Đã sửa công việc:\nCũ: {old_task}\nMới: {new_task_description}')
      else:
         await ctx.send('Không tìm thấy công việc với số thứ tự này.')

   @commands.command(name='complete')
   async def complete_task(self, ctx, index: int, status: int):
      tasks_ref, tasks = await self.get_user_tasks(ctx)

      # Check if the status is valid
      if not (status == 0 or status == 1):
         await ctx.send('Trạng thái không hợp lệ. Vui lòng sử dụng 0 (chưa hoàn thành) hoặc 1 (đã hoàn thành).')
         return
      
      # Check if the task index is valid
      if tasks and 0 < index <= len(tasks):
         task_id = list(tasks.keys())[index-1]

         # Update the task status
         updates = {
            'completed': bool(status),
            'overdue': False
         }
         tasks_ref.document(task_id).update(updates)
         status_text = "hoàn thành" if status == 1 else "chưa hoàn thành"
         await ctx.send(f'Đã đánh dấu công việc {index} là {status_text}.')
      else:
         await ctx.send('Không tìm thấy công việc với số thứ tự này.')

   @commands.command(name='delete')
   async def delete_task(self, ctx, index: int):
      tasks_ref, tasks = await self.get_user_tasks(ctx)

      # Check if the task index is valid
      if tasks and 0 < index <= len(tasks):
         # Get selected task ID
         task_id = list(tasks.keys())[index-1]

         # Save the deleted task for the response message
         deleted_task = tasks[task_id]

         tasks_ref.document(task_id).delete()
         await ctx.send(f'Đã xóa công việc: {deleted_task["task"]}')
      else:
         await ctx.send('Không tìm thấy công việc với số thứ tự này.')

   @commands.command(name='deadline')
   async def set_deadline(self, ctx, index: int, deadline: str):
      tasks_ref, tasks = await self.get_user_tasks(ctx)

      # Check if the task index is valid
      if tasks and 0 < index <= len(tasks):
         # Validate the new deadline
         is_valid, result = util.is_valid_date(deadline)
         if not is_valid:
            await ctx.send(result)
            return
         
         # get selected task ID
         task_id = list(tasks.keys())[index-1]
         # Update the task deadline
         tasks_ref.document(task_id).update({
            'deadline': result.isoformat(),
            'overdue': False
         })

         await ctx.send(f'Đã đặt hạn cho công việc {index}: {deadline}')
      else:
         await ctx.send('Không tìm thấy công việc với số thứ tự này.')

   @commands.command(name='list_w')
   async def list_this_week_tasks(self, ctx):
      tasks_ref, tasks = await self.get_user_tasks(ctx)
      # Check tasks list is empty
      if not tasks:
         await ctx.send('Danh sách công việc của bạn trống.')
         return

      # Update overdue status before listing
      await self.check_overdue_tasks(tasks_ref, tasks)
      tasks_ref, tasks = await self.get_user_tasks(ctx)

      # Calculate this week's date range
      today = date.today()
      start_of_week = today - timedelta(days=today.weekday())
      end_of_week = start_of_week + timedelta(days=6)
      
      # Filter and format tasks for this week
      task_list = []
      task_count = 0
      for task_info in util.sort_tasks(tasks):
         value = task_info['data']
         if value['completed']:
            continue
         
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

   @commands.command(name='list_nw')
   async def list_next_week_tasks(self, ctx):
      tasks_ref, tasks = await self.get_user_tasks(ctx)
      if not tasks:
         await ctx.send('Danh sách công việc của bạn trống.')
         return

      await self.check_overdue_tasks(tasks_ref, tasks)
      tasks_ref, tasks = await self.get_user_tasks(ctx)

      # Calculate next week's date range
      today = date.today()
      start_of_next_week = today + timedelta(days=(7 - today.weekday()))
      end_of_next_week = start_of_next_week + timedelta(days=6)
      
      # Filter and format tasks for next week
      task_list = []
      task_count = 0
      for task_info in util.sort_tasks(tasks):
         value = task_info['data']
         if value['completed']:
            continue
         
         if value['deadline']:
            deadline_date = datetime.fromisoformat(value['deadline']).date()
            if start_of_next_week <= deadline_date <= end_of_next_week:
               deadline = f"Exp: {deadline_date.strftime('%d/%m/%Y')}"
               status = 'O' if value.get('overdue', False) else '✗'
               task_count += 1
               task_list.append(f"{task_count}. [{status}] - {value['task']} - {deadline}")

      if task_list:
         formatted_list = '\n'.join(task_list)
         legend = "\nChú thích:\n[✗] - Chưa hoàn thành\n[O] - Quá hạn"
         await ctx.send(f'Danh sách công việc chưa hoàn thành trong tuần tới:\n{formatted_list}{legend}')
      else:
         await ctx.send('Không có công việc chưa hoàn thành trong tuần tới.')

   @commands.command(name='clear_todo')
   async def clear_tasks(self, ctx):
      # Get a reference to the user's tasks collection
      tasks_ref = self.get_user_ref(ctx)
      tasks = tasks_ref.stream()

      # Delete all tasks
      for task in tasks:
         task.reference.delete()
      await ctx.send("Đã xóa tất cả công việc.")

   @commands.command(name='todo')
   async def help_command(self, ctx):
      try:
         with open('features/todo/todo_help.txt', 'r', encoding='utf-8') as file:
            help_content = file.read()
         await ctx.send(f'```{help_content}```') 
      except Exception as e:
         await ctx.send(f"Có lỗi xảy ra: {str(e)}")

   async def check_overdue_tasks(self, tasks_ref, tasks):
      if not tasks:
         return

      current_date = date.today()
      batch = self.db.batch()

      # Check each task's deadline and update overdue status if necessary
      for doc_id, value in tasks.items():
         if not value['completed'] and value['deadline']:
            deadline_date = datetime.fromisoformat(value['deadline']).date()
            if deadline_date < current_date and not value.get('overdue', False):
               doc_ref = tasks_ref.document(doc_id)
               batch.update(doc_ref, {'overdue': True})

      batch.commit()

async def setup(bot)-> None:
   # Setup function to add the TodoCog to the bot.
   await bot.add_cog(TodoCog(bot))
