from storage import load_tasks, save_tasks


def show_menu():
    print("\n === Task Tracker CLI ====")
    print("1. Add Task")
    print("2. View Tasks")
    print("3. Delete Task")
    print("4. Update Task")
    print("5. Mark Task Comppleted")
    print("6. Exit")


def main():
    tasks = load_tasks()
    while True:
        show_menu()
        choice = input("Enter your choice: ")
        if choice == "1":
            description = input("Enter task decription:  ")
            task_id = len(tasks) + 1
            task = {"id": task_id, "description": description, "status": "Pending"}
            tasks.append(task)
            print(f"Task added to list with ID {task_id} .")
            save_tasks(tasks)
        elif choice == "2":
            if not tasks:
                print("Task List is empty")
            else:
                print("Your task list:")
                for task in tasks:
                    print(
                        f"ID : {task['id']} | Title : {task['description']} | Status : {task['status']} "
                    )
        elif choice == "3":
            if not tasks:
                print("No task to be deleted")
            else:
                try:
                    task_id = int(
                        input("Enter the ID of the task you want to delete: ")
                    )
                    for task in tasks:
                        if task["id"] == task_id:
                            tasks.remove(task)
                            print(f" Task  id with {task_id} is removed")
                            save_tasks(tasks)
                            break
                    else:
                        print("Task_ID not found")
                except ValueError:
                    print("Invalid input")
        elif choice == "4":
            if not tasks:
                print("No task to be updated")
            else:
                try:
                    task_id = int(
                        input("Enter the ID of the task you want to update: ")
                    )
                    variable_to_update = input(
                        f"Description of id :{task_id} is changed to : "
                    )
                    for task in tasks:
                        if task["id"] == task_id:
                            task["description"] = variable_to_update
                            print(f"Description with id :{task_id} is updated")
                            save_tasks(tasks)
                except ValueError:
                    print("Invalid input")
        elif choice == "5":
            if not tasks:
                print("No task to be marked completed")
            else:
                try:
                    task_id = int(input("Enter task_id to marked as completed: "))
                    for task in tasks:
                        if task["id"] == task_id:
                            task["status"] = "Completed"
                            print(f"ID with {task_id} marked done")
                            save_tasks(tasks)
                            break
                    else:
                        print("Task_ID not found")
                except ValueError:
                    print("Invalid Input")
        elif choice == "6":
            print("\n === Goodbye ====")
        else:
            print("Invalid choice. Try again")


if __name__ == "__main__":
    main()
