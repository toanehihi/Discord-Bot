from datetime import date, datetime
'''
   Check the date is valid or not
   and the date is not in the past.
'''
def is_valid_date(date_str):
   try:
      day, month, year = map(int, date_str.split('/'))
      input_date = date(year, month, day)
      current_date = date.today()
      if input_date < current_date:
         return False, "Ngày nhập đã qua - không hợp lệ."
      return True, input_date
   except ValueError:
      return False, "Ngày nhập không hợp lệ."

'''
   Sorts a list of tasks by priority:
   1. Incomplete tasks, sorted by days until the deadline (soonest first).
   2. Completed tasks.
   3. Overdue tasks.
'''
def sort_tasks(tasks):
   current_date = date.today()

   task_list = []
   for key, value in tasks.items():
      task_info = {
         'key': key,
         'data': value,
         'days_until_deadline': float('inf') # Default to infinity for tasks without a deadline
      }

      #Calculate the number of days until the deadline
      deadline_date = datetime.fromisoformat(value['deadline']).date()
      task_info['days_until_deadline'] = (deadline_date - current_date).days

      task_list.append(task_info)

   # Categorize tasks into incomplete, completed, and overdue
   incomplete_tasks = []
   completed_tasks = []
   overdue_tasks = []

   for task in task_list:
      if task['data'].get('overdue', False):
         overdue_tasks.append(task)
      elif task['data']['completed']:
         completed_tasks.append(task)
      else:
         incomplete_tasks.append(task)

   # Sort incomplete tasks by days
   incomplete_tasks.sort(key=lambda x: x['days_until_deadline'])

   return incomplete_tasks + completed_tasks + overdue_tasks

