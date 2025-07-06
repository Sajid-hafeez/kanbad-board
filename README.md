# Professional Kanban Board Application

A professional-grade Kanban board application built with pure Python and Streamlit. The application allows you to manage your tasks efficiently and save them to CSV files for persistence.

## Features

- Move tasks between columns (To Do, In Progress, Done)
- Create, edit, and archive tasks
- Track task details including title, description, due date, priority, and assignee
- Persistent storage with CSV files
- Modern, responsive UI design
- Visual indicators for task priorities and due dates
- Task filtering and search
- Task statistics and metrics

## Setup and Installation

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   streamlit run app.py
   ```
   Or use the included batch file:
   ```
   run_kanban.bat
   ```

## Project Structure

```
kanban-board/
├── app.py               # Main Streamlit application
├── data/                # Data storage
│   └── tasks.csv        # CSV file for task persistence
├── requirements.txt     # Required Python packages
└── run_kanban.bat       # Batch file to run the application
```

## Usage

1. Add new tasks by clicking "Create New Task" in the sidebar
2. Move tasks between columns using the action buttons under each task
3. Edit tasks by clicking the "Edit" button on any task
4. Archive completed tasks individually or use the "Archive All" button in the Done column
5. Search tasks using the search box at the top of the board
6. View task statistics and archived tasks in the sidebar

## Technologies Used

- Python/Streamlit for the backend and UI
- Pandas for data manipulation
- CSV for data persistence

## License

© 2025
