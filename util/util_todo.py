from datetime import date, datetime, timedelta


# Check the date is valid or not
# and the date is not in the past.
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

# Helper function to format tasks
def format_tasks(task_list, status_marker, count, result):
   for task in task_list:
      count += 1
      for task_id, task_info in task.items():  # Unpack the task dictionary
         deadline = format_deadline(task_info["deadline"], status_marker == "[✗]")
         result.append(f'{count}. {status_marker}  -  {task_info["task"]}  -  {deadline}')

'''
   Format deadline message before show
'''
def format_deadline(date_str, is_incomplete=False):
   # Convert the string to a datetime object
   deadline_date = datetime.fromisoformat(date_str)
   
   # Format the deadline message
   deadline_format = f'Deadline: {deadline_date.strftime("%d/%m/%Y")} '
   
   if is_incomplete:
      # Calculate the number of days left until the deadline
      today = datetime.now().date()
      days_left = (deadline_date.date() - today).days
      
      # check
      if days_left > 0:
         deadline_format += f"(Còn {days_left} ngày)"
      elif days_left == 0:
         deadline_format += "(Hôm nay)"
   
   return deadline_format

'''
   Filter tasks by a specific condition.
'''
def filter_task_by_condition(tasks, condition_func):
   filtered_data = [task for task in tasks if condition_func(list(task.values())[0])]
   return filtered_data
# Define the condition functions
def is_completed(task):
   return task['completed'] == True

def is_incomplete(task):
   return task['completed'] == False and task['overdue'] == False

def is_overdue(task):
   return task['overdue'] == True

def check_task_deadline_and_overdue(task):
   return task['overdue'] == False and task['deadline'] < date.today().isoformat()

def is_task_in_this_week(task):
   today = date.today() # get the current date
   deadline_date = datetime.fromisoformat(task['deadline']).date() # get the deadline date
   start_of_week = today - timedelta(days=today.weekday()) # get the start of the week
   end_of_week = start_of_week + timedelta(days=6)  # get the end of the week
   return start_of_week <= deadline_date <= end_of_week and task['completed'] == False and task['overdue'] == False # check the deadline date is in this week or not

def is_task_in_next_week(task):
   today = date.today() # get the current date
   deadline_date = datetime.fromisoformat(task['deadline']).date() # get the deadline date
   start_of_next_week = today + timedelta(weeks=1) - timedelta(days=today.weekday()) # get the start of the next week
   end_of_next_week = start_of_next_week + timedelta(days=6)  # get the end of the next week
   return start_of_next_week <= deadline_date <= end_of_next_week and task['completed'] == False and task['overdue'] == False # check the deadline date is in next week or not

'''
   Get tasks by priority
'''
def get_tasks_by_priority(tasks):
   tasks_are_incomplete = filter_task_by_condition(tasks, is_incomplete)
   tasks_are_completed = filter_task_by_condition(tasks, is_completed)
   tasks_are_overdue = filter_task_by_condition(tasks, is_overdue)
   return tasks_are_incomplete + tasks_are_completed + tasks_are_overdue

'''
   Get the task info by task number
'''
def get_task_info_by_task_number(tasks, task_number):
   # Get tasks by priority
   tasks_priority = get_tasks_by_priority(tasks)
   # Get the task ID 
   task_id = list(tasks_priority[task_number - 1].keys())[0]
   # Get the task info
   task_info = tasks_priority[task_number - 1][task_id]
   return task_id, task_info
