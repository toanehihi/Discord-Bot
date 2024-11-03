import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta, date
from discord.ext import commands

import util.util_todo as util

# Setup function to add the TodoCog to the bot.
async def setup(bot)-> None:
   await bot.add_cog(TodoCog(bot))

class TodoCog(commands.Cog,name="Todo"):
   def __init__(self, bot):
      self.bot = bot

      # Initialize Firebase
      cred = credentials.Certificate('config/todo-app-key.json')
      if not firebase_admin._apps:
         firebase_admin.initialize_app(cred)
      self.db = firestore.client()

   def get_user_ref(self, ctx):
      # Get a reference to a user's tasks collection in Firebase.
      # users -> user_id -> tasks -> ...
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
      tasks = []
      for doc in docs:
         task = {}
         task[doc.id] = doc.to_dict()
         tasks.append(task)
      return tasks_ref, tasks

   @commands.command(name='test',description="")
   async def test(self, ctx):
      task_ref, tasks = await self.get_user_tasks(ctx)
      rs = util.get_tasks_by_priority(tasks)
      await ctx.send(f'{rs}')

   @commands.command(name='add',description="Thêm một task mới")
   async def add_task(self, ctx, *, task_and_deadline: str):
      # Get name of the user in discord
      user_name = ctx.author.display_name

      # Get the user's tasks reference
      tasks_ref = self.get_user_ref(ctx)

      # Split the task and deadline from the input
      # Example: !add Finish homework 11/11/2024
      parts = task_and_deadline.rsplit(' ', 1)
      task = parts[0]  # Finish homework
      deadline = parts[1] # 11/11/2024
      
      # Validate the deadline date format (dd/mm/yyyy)
      is_valid, result = util.is_valid_date(deadline)
      if not is_valid:
         await ctx.send(result)
         return
      
      # Create new task object with default values
      new_task = {
         "task": task,
         "completed": False,
         "overdue": False,
         "deadline": result.isoformat(),
         "created_at": datetime.now().isoformat()
      }
      
      # add new task to the user's tasks collection
      tasks_ref.add(new_task)
      await ctx.send(f'[{user_name}] Đã thêm công việc: {task}')

   @commands.command(name='list', description="Liệt kê tất cả các task")
   async def list_tasks(self, ctx):
      await self.update_overdue_tasks(ctx)

      # Get name of the user in discord
      user_name = ctx.author.display_name

      # Get the user's tasks
      tasks_ref, tasks = await self.get_user_tasks(ctx)

      # Check tasks is empty then exit
      if not tasks:
         await ctx.send(f'[{user_name}] Bạn không có công việc nào.')
         return

      # Filter tasks by status
      tasks_are_incomplete = util.filter_task_by_condition(tasks, util.is_incomplete)
      tasks_are_completed = util.filter_task_by_condition(tasks, util.is_completed)
      tasks_are_overdue = util.filter_task_by_condition(tasks, util.is_overdue)

      result = []
      count = 0
      # Format tasks based on their status
      if tasks_are_incomplete:
         util.format_tasks(tasks_are_incomplete, "[✗]", count, result)
      if tasks_are_completed:
         util.format_tasks(tasks_are_completed, "[✓]", count, result)
      if tasks_are_overdue:
         util.format_tasks(tasks_are_overdue, "[O]", count, result)

      # Display the tasks in a formatted message
      tasks_formatted = '\n'.join(result)
      await ctx.send(f'[{user_name}] Danh sách công việc:\n{tasks_formatted}')

   @commands.command(name='list_w', description="Liệt kê tất cả các task cần hoàn thành trong tuần")
   async def list_task_this_weak(self, ctx):
      await self.update_overdue_tasks(ctx)

      # Get name of the user in discord
      user_name = ctx.author.display_name

      # Get the user's tasks
      tasks_ref, tasks = await self.get_user_tasks(ctx)
      
      # Filter tasks in this week
      tasks_this_week = util.filter_task_by_condition(tasks, util.is_task_in_this_week)
      if not tasks_this_week:
         await ctx.send(f'[{user_name}] Bạn không có công việc nào trong tuần này.')
         return # Exit if no tasks are in this week
      
      # Format the tasks
      result = []
      count = 0
      util.format_tasks(tasks_this_week, "[✗]", count, result)

      # Display the tasks in a formatted message
      tasks_formatted = '\n'.join(result)
      await ctx.send(f'[{user_name}] Danh sách công việc cần làm trong tuần này:\n{tasks_formatted}')

   @commands.command(name='list_nw', description="Liệt kê tất cả các task cần hoàn thành trong tuần sau")
   async def list_task_next_weak(self, ctx):
      await self.update_overdue_tasks(ctx)

      # Get name of the user in discord
      user_name = ctx.author.display_name

      # Get the user's tasks
      tasks_ref, tasks = await self.get_user_tasks(ctx)
      
      # Filter tasks in next week
      tasks_next_week = util.filter_task_by_condition(tasks, util.is_task_in_next_week)
      if not tasks_next_week:
         await ctx.send(f'[{user_name}] Bạn không có công việc nào trong tuần sau.')
         return # Exit if no tasks are in next week

      # Format the tasks
      result = []
      count = 0
      util.format_tasks(tasks_next_week, "[✗]", count, result)

      # Display the tasks in a formatted message
      tasks_formatted = '\n'.join(result)
      await ctx.send(f'[{user_name}] Danh sách công việc cần làm trong tuần sau:\n{tasks_formatted}')

   @commands.command(name='complete', description="Đánh dấu một task là đã hoàn thành hoặc chưa hoàn thành")
   async def complete_task(self, ctx, task_number: int, task_status: int):
      # Get user's name in discord
      user_name = ctx.author.display_name

      # Get the user's tasks from Firebase
      tasks_ref, tasks = await self.get_user_tasks(ctx)

      # Check if the task number is valid
      if task_number < 1 or task_number > len(tasks):
         await ctx.send(f'[{user_name}] Số thứ tự công việc không hợp lệ.')
         return

      # Check if the task status is valid
      # 0: Incomplete, 1: Completed
      if task_status not in [0, 1]:
         await ctx.send(f'[{user_name}] Trạng thái công việc không hợp lệ.')
      
      # Get the task ID and info
      task_id, task_info = util.get_task_info_by_task_number(tasks, task_number)

      # If the task is overdue, it cannot be marked
      if task_info['overdue']:
         await ctx.send(f'[{user_name}] Công việc đã quá hạn không thể đánh dấu.')
         return

      # Update the task's status in Firebase
      task_ref = self.get_user_ref(ctx)
      doc_ref = (task_ref
                     .document(task_id)
                     .update({'completed': bool(task_status)})
               )
      await ctx.send(f'[{user_name}] Đã cập nhật trạng thái công việc.')

   @commands.command(name='edit', description="Chỉnh sửa nội dung của task")
   async def edit_task(self, ctx, task_number: int, *, new_task: str):
      # Get user's name in discord
      user_name = ctx.author.display_name

      # Get the user's tasks from Firebase
      tasks_ref, tasks = await self.get_user_tasks(ctx)

      # Check if the task number is valid
      if task_number < 1 or task_number > len(tasks):
         await ctx.send(f'[{user_name}] Số thứ tự công việc không hợp lệ.')
         return
      
      # Get the task ID and info
      task_id, task_info = util.get_task_info_by_task_number(tasks, task_number)

      # Update the task's description
      doc = (tasks_ref
                  .document(task_id)
                  .update({'task': new_task})
            )
      
      await ctx.send(f'[{user_name}] Đã cập nhật nội dung công việc.')

   @commands.command(name='deadline', description="Chỉnh sửa deadline của task")
   async def edit_deadline(self, ctx, task_number: int, new_deadline: str):
      # Get user's name in discord
      user_name = ctx.author.display_name

      # Get the user's tasks from Firebase
      tasks_ref, tasks = await self.get_user_tasks(ctx)

      # Check if the task number is valid
      if task_number < 1 or task_number > len(tasks):
         await ctx.send(f'[{user_name}] Số thứ tự công việc không hợp lệ.')
         return
      
      # check if the new deadline is valid
      is_valid, result = util.is_valid_date(new_deadline)
      if not is_valid:
         await ctx.send(result)
         return

      # Get the task ID and info
      task_id, task_info = util.get_task_info_by_task_number(tasks, task_number)

      updated_deadline = {
         'deadline': result.isoformat(),
      }
      # If the task is overdue, update the overdue status
      if task_info['overdue']:
         updated_deadline = {
            'overdue': False,
         }

      # Update the task's deadline
      doc = (tasks_ref
                  .document(task_id)
                  .update(updated_deadline)
            )

      await ctx.send(f'[{user_name}] Đã cập nhật deadline của công việc.')

   @commands.command(name='delete', description="Xóa một task")
   async def delete_task(self, ctx, task_number: int):
      # Get user's name in discord
      user_name = ctx.author.display_name

      # Get the user's tasks from Firebase
      tasks_ref, tasks = await self.get_user_tasks(ctx)

      # Check if the task number is valid
      if task_number < 1 or task_number > len(tasks):
         await ctx.send(f'[{user_name}] Số thứ tự công việc không hợp lệ.')
         return
      
      # Get the task ID and info
      task_id, task_info = util.get_task_info_by_task_number(tasks, task_number)

      # Delete the task from Firebase
      doc = (tasks_ref
                  .document(task_id)
                  .delete()
            )

      await ctx.send(f'[{user_name}] Đã xóa công việc.')

   @commands.command(name='clear_todo', description="Xóa tất cả các task")
   async def clear_tasks(self, ctx):
      # Get user's name in discord
      user_name = ctx.author.display_name

      # Get the user's tasks from Firebase
      tasks_ref, tasks = await self.get_user_tasks(ctx)

      # Check if the user has any tasks
      if not tasks:
         await ctx.send(f'[{user_name}] Bạn không có công việc nào để xoá.')
         return

      # Delete all tasks from Firebase
      for task in tasks:
         for task_id, task_info in task.items():
            doc = tasks_ref.document(task_id).delete()

      await ctx.send(f'[{user_name}] Đã xóa tất cả công việc.')

   @commands.command(name='todo',description="Hiển thị danh sách các lệnh")
   async def help_command(self, ctx):
      try:
         with open('util/todo_help.txt', 'r', encoding='utf-8') as file:
            help_content = file.read()
         await ctx.send(f'```{help_content}```') 
      except Exception as e:
         await ctx.send(f"Có lỗi xảy ra: {str(e)}")

   async def update_overdue_tasks(self, ctx):
      # Get the user's tasks from Firebase
      tasks_ref, tasks = await self.get_user_tasks(ctx)

      # If tasks is empty, exit
      if not tasks:
         return

      # Filter tasks by incomplete and not overdue
      update_task_overdue = util.filter_task_by_condition(tasks, util.check_task_deadline_and_overdue)
      if not update_task_overdue:
         return  # Exit if no tasks are overdue

      for task in update_task_overdue:
         for task_id, task_info in task.items(): # Unpack the task dictionary
            # Update the task's overdue status
            tasks_ref.document(task_id).update({'overdue': True})






