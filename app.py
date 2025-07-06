import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import uuid
import time

# Set page configuration
st.set_page_config(
    page_title="Professional Kanban Board",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define file paths
DATA_PATH = os.path.join("data", "tasks.csv")

# Ensure the data directory exists
os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)

# Function to validate and repair the CSV file if needed
def validate_csv_file():
    """Validates the CSV file and repairs it if necessary."""
    try:
        # Check if the file exists
        if not os.path.exists(DATA_PATH):
            print(f"CSV file not found at {DATA_PATH}, creating empty file")
            # Create a new empty DataFrame with the required columns
            empty_df = pd.DataFrame(columns=["title", "description", "status", "due_date", 
                                           "priority", "assignee", "created_date", "id", "archived"])
            # Save it
            empty_df.to_csv(DATA_PATH, index=False, encoding='utf-8')
            return True
            
        # Try to read the file
        try:
            tasks_df = pd.read_csv(DATA_PATH)
            print(f"CSV validation successful: {len(tasks_df)} tasks found")
            return True
        except Exception as e:
            print(f"CSV validation failed: {e}")
            
            # Try to run the rebuild script
            try:
                import rebuild_csv
                success = rebuild_csv.rebuild_csv()
                if success:
                    print("CSV rebuild successful!")
                    return True
                else:
                    print("CSV rebuild failed, creating a new file")
                    # Create a new empty file as a last resort
                    empty_df = pd.DataFrame(columns=["title", "description", "status", "due_date", 
                                                  "priority", "assignee", "created_date", "id", "archived"])
                    empty_df.to_csv(DATA_PATH, index=False, encoding='utf-8')
                    return True
            except ImportError:
                print("Rebuild module not available, creating a new file")
                # Create a new empty file
                empty_df = pd.DataFrame(columns=["title", "description", "status", "due_date", 
                                               "priority", "assignee", "created_date", "id", "archived"])
                empty_df.to_csv(DATA_PATH, index=False, encoding='utf-8')
                return True
    except Exception as e:
        print(f"CSV validation error: {e}")
        return False

# Validate the CSV file at startup
validate_csv_file()

# Function to load tasks from CSV
def load_tasks(include_archived=False):
    if os.path.exists(DATA_PATH):
        try:
            tasks_df = pd.read_csv(DATA_PATH)
            
            # Ensure description is a string, replace NaN with empty string
            if 'description' in tasks_df.columns:
                tasks_df['description'] = tasks_df['description'].fillna('')
            
            # Ensure archived column exists
            if 'archived' not in tasks_df.columns:
                tasks_df['archived'] = False
            
            # Filter out archived tasks unless specifically requested
            if not include_archived:
                tasks_df = tasks_df[tasks_df['archived'] != True]
                
            return tasks_df
        except Exception as e:
            st.error(f"Error loading tasks: {e}")
            return pd.DataFrame(columns=["title", "description", "status", "due_date", "priority", "assignee", "created_date", "id", "archived"])
    else:
        return pd.DataFrame(columns=["title", "description", "status", "due_date", "priority", "assignee", "created_date", "id", "archived"])

# Function to save tasks to CSV
def save_tasks(tasks_df):
    try:
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
        
        # Log the save operation
        print(f"Saving {len(tasks_df)} tasks to {DATA_PATH}")
        
        # Force sync to disk with explicit encoding and proper line ending
        # Use try-except for better error handling during save
        try:
            # Clean the DataFrame before saving
            for col in tasks_df.columns:
                if tasks_df[col].dtype == 'object':  # Only process string/object columns
                    tasks_df[col] = tasks_df[col].astype(str).apply(lambda x: x.replace('\r\n', ' ').replace('\n', ' '))
            
            # Save with explicit parameters for robustness
            tasks_df.to_csv(DATA_PATH, index=False, encoding='utf-8', lineterminator='\n')
            
            # Verify the file was written by explicitly reading it back
            if os.path.exists(DATA_PATH):
                # Try to read the file back to verify it's valid
                pd.read_csv(DATA_PATH)
                print(f"File {DATA_PATH} successfully saved and verified with size {os.path.getsize(DATA_PATH)} bytes")
                return True
            else:
                st.error(f"File {DATA_PATH} was not created")
                return False
        except Exception as save_error:
            st.error(f"Error during CSV write operation: {save_error}")
            import traceback
            print(f"CSV save error: {traceback.format_exc()}")
            
            # Emergency fallback - try saving with different parameters
            try:
                tasks_df.to_csv(DATA_PATH, index=False, encoding='utf-8-sig', quoting=1)
                print("Emergency save successful with alternate parameters")
                return True
            except:
                print("Even emergency save failed")
                return False
            
    except Exception as e:
        st.error(f"Error saving tasks: {e}")
        import traceback
        print(traceback.format_exc())
        return False

# Function to create a new task
def create_task(title, description, status, due_date, priority, assignee):
    tasks_df = load_tasks(include_archived=True)
    
    # Handle None or empty description
    if description is None or pd.isna(description):
        description = ''
    
    # Create a new task
    new_task = {
        "title": title,
        "description": description,
        "status": status,
        "due_date": due_date,
        "priority": priority,
        "assignee": assignee,
        "created_date": datetime.now().strftime("%Y-%m-%d"),
        "id": str(uuid.uuid4()),
        "archived": False
    }
    
    # Add to DataFrame
    tasks_df = pd.concat([tasks_df, pd.DataFrame([new_task])], ignore_index=True)
    
    # Save to CSV
    save_tasks(tasks_df)
    return True

# Function to update a task
def update_task(task_id, title, description, status, due_date, priority, assignee):
    tasks_df = load_tasks(include_archived=True)
    
    # Handle None or empty description
    if description is None or pd.isna(description):
        description = ''
    
    # Find the task by ID
    if 'id' not in tasks_df.columns:
        tasks_df['id'] = [str(uuid.uuid4()) for _ in range(len(tasks_df))]
    
    task_idx = tasks_df[tasks_df['id'] == task_id].index
    
    if len(task_idx) == 0:
        return False
    
    # Update the task
    tasks_df.loc[task_idx, 'title'] = title
    tasks_df.loc[task_idx, 'description'] = description
    tasks_df.loc[task_idx, 'status'] = status
    tasks_df.loc[task_idx, 'due_date'] = due_date
    tasks_df.loc[task_idx, 'priority'] = priority
    tasks_df.loc[task_idx, 'assignee'] = assignee
    
    # Ensure task is not archived if it's being updated
    tasks_df.loc[task_idx, 'archived'] = False
    
    # Save to CSV
    save_tasks(tasks_df)
    return True

# Function to delete a task (archive it)
def delete_task(task_id):
    tasks_df = load_tasks(include_archived=True)
    
    # Find the task by ID
    if 'id' not in tasks_df.columns:
        tasks_df['id'] = [str(uuid.uuid4()) for _ in range(len(tasks_df))]
    
    # Mark the task as archived instead of removing it
    task_idx = tasks_df[tasks_df['id'] == task_id].index
    if len(task_idx) > 0:
        tasks_df.loc[task_idx, 'archived'] = True
    
    # Save to CSV
    save_tasks(tasks_df)
    return True

# Function to clear all done tasks (archive them)
def clear_done_tasks():
    tasks_df = load_tasks(include_archived=True)
    
    # Mark 'Done' tasks as archived instead of removing them
    tasks_df.loc[tasks_df['status'] == 'Done', 'archived'] = True
    
    # Save to CSV
    save_tasks(tasks_df)
    return True

# Function to update task status
def update_task_status(task_id, new_status):
    try:
        tasks_df = load_tasks(include_archived=True)
        
        # Find the task by ID
        if 'id' not in tasks_df.columns:
            tasks_df['id'] = [str(uuid.uuid4()) for _ in range(len(tasks_df))]
        
        task_idx = tasks_df[tasks_df['id'] == task_id].index
        
        if len(task_idx) == 0:
            st.error(f"Task with ID {task_id} not found")
            return False
        
        # Log the status change for debugging
        old_status = tasks_df.loc[task_idx, 'status'].iloc[0]
        print(f"Updating task {task_id} status: {old_status} -> {new_status}")
        
        # Update the status
        tasks_df.loc[task_idx, 'status'] = new_status
        
        # Ensure task is not archived if it's being moved
        tasks_df.loc[task_idx, 'archived'] = False
        
        # Save to CSV with explicit flush to ensure it's written to disk
        success = save_tasks(tasks_df)
        
        # Verify the save
        if success:
            # Double-check by reloading
            verify_df = load_tasks(include_archived=True)
            verify_task = verify_df[verify_df['id'] == task_id]
            if len(verify_task) > 0 and verify_task['status'].iloc[0] == new_status:
                print(f"Task status update verified: {task_id} is now {new_status}")
                return True
            else:
                st.error("Task update failed verification")
                return False
        return success
    except Exception as e:
        st.error(f"Error updating task status: {e}")
        return False

# Function to determine the color for priority badges
def get_priority_color(priority):
    if priority == "High":
        return "red"
    elif priority == "Medium":
        return "orange"
    elif priority == "Low":
        return "green"
    else:
        return "blue"

# Function to determine if a date is overdue or due soon
def get_due_status(due_date_str):
    try:
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
        today = datetime.now().date()
        
        if due_date.date() < today:
            return "overdue"
        elif (due_date.date() - today).days <= 2:
            return "due-soon"
        else:
            return "normal"
    except:
        return "normal"

# Function to restore all archived tasks
def restore_all_archived_tasks():
    tasks_df = load_tasks(include_archived=True)
    tasks_df['archived'] = False
    save_tasks(tasks_df)
    return True

# Initialize session state
if 'show_task_form' not in st.session_state:
    st.session_state.show_task_form = False

if 'selected_task_id' not in st.session_state:
    st.session_state.selected_task_id = None

if 'filter_text' not in st.session_state:
    st.session_state.filter_text = ""

# App title and description
st.title("Professional Kanban Board")
st.markdown("Manage your tasks with this interactive Kanban board")

# Create columns for the app layout with more space for the board
board_col, sidebar_col = st.columns([4, 1])

with board_col:
    # Create the three columns for the Kanban board
    st.subheader("Task Board")
    
    # Filter controls
    filter_text = st.text_input("Search tasks", key="filter_input", value=st.session_state.filter_text)
    st.session_state.filter_text = filter_text
    
    # Define our columns
    todo_col, inprogress_col, done_col = st.columns(3)
    
    # Load tasks
    tasks_df = load_tasks()
    
    # Apply text filter if needed
    if filter_text:
        tasks_df = tasks_df[
            tasks_df['title'].str.contains(filter_text, case=False) | 
            tasks_df['description'].str.contains(filter_text, case=False)
        ]
    
    # Separate tasks by status
    todo_tasks = tasks_df[tasks_df['status'] == 'To Do'].to_dict('records')
    inprogress_tasks = tasks_df[tasks_df['status'] == 'In Progress'].to_dict('records')
    done_tasks = tasks_df[tasks_df['status'] == 'Done'].to_dict('records')
    
    # Render To Do column
    with todo_col:
        st.markdown(f"### To Do ({len(todo_tasks)})")
        
        for task in todo_tasks:
            task_id = task.get('id', '')
            with st.container():
                # Create a box with colored left border based on priority
                priority_color = get_priority_color(task.get('priority', 'Medium'))
                
                # Create CSS for the task card
                st.markdown(f"""
                <style>
                    .task-card-{task_id} {{
                        border-left: 4px solid {priority_color};
                        padding: 10px;
                        border-radius: 5px;
                        background-color: #2a2a3c;
                        margin-bottom: 10px;
                        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                    }}
                    .task-title-{task_id} {{
                        font-weight: bold;
                        margin-bottom: 5px;
                    }}
                    .task-desc-{task_id} {{
                        font-size: 0.9em;
                        color: #a1a8c9;
                        margin-bottom: 5px;
                    }}
                    .task-meta-{task_id} {{
                        display: flex;
                        justify-content: space-between;
                        font-size: 0.8em;
                    }}
                    .priority-badge-{task_id} {{
                        background-color: {priority_color}33;
                        color: {priority_color};
                        padding: 2px 6px;
                        border-radius: 10px;
                        font-size: 0.7em;
                    }}
                </style>
                """, unsafe_allow_html=True)
                
                # Create the task card with HTML
                due_status = get_due_status(task.get('due_date', ''))
                due_color = "red" if due_status == "overdue" else "orange" if due_status == "due-soon" else "white"
                
                st.markdown(f"""
                <div class="task-card-{task_id}">
                    <div class="task-title-{task_id}">{task.get('title', 'No Title')}</div>
                    <div class="task-desc-{task_id}">{task.get('description', '')[:50] + ('...' if len(task.get('description', '')) > 50 else '')}</div>
                    <div class="task-meta-{task_id}">
                        <span style="color: {due_color}">Due: {task.get('due_date', 'N/A')}</span>
                        <span class="priority-badge-{task_id}">{task.get('priority', 'Medium')}</span>
                    </div>
                    <div style="font-size: 0.8em; margin-top: 5px;">{task.get('assignee', '')}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Add action buttons below the card
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏️ Edit", key=f"edit_{task_id}"):
                        st.session_state.selected_task_id = task_id
                        st.session_state.show_task_form = True
                        st.rerun()
                        
                with col2:
                    if st.button("▶️ Start", key=f"start_{task_id}"):
                        update_task_status(task_id, "In Progress")
                        st.success(f"Task '{task.get('title')}' moved to In Progress")
                        time.sleep(0.5)  # Small delay for better user feedback
                        st.rerun()
    
    # Render In Progress column
    with inprogress_col:
        st.markdown(f"### In Progress ({len(inprogress_tasks)})")
        
        for task in inprogress_tasks:
            task_id = task.get('id', '')
            with st.container():
                # Create a box with colored left border based on priority
                priority_color = get_priority_color(task.get('priority', 'Medium'))
                
                # Create CSS for the task card
                st.markdown(f"""
                <style>
                    .task-card-{task_id} {{
                        border-left: 4px solid {priority_color};
                        padding: 10px;
                        border-radius: 5px;
                        background-color: #2a2a3c;
                        margin-bottom: 10px;
                        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                    }}
                    .task-title-{task_id} {{
                        font-weight: bold;
                        margin-bottom: 5px;
                    }}
                    .task-desc-{task_id} {{
                        font-size: 0.9em;
                        color: #a1a8c9;
                        margin-bottom: 5px;
                    }}
                    .task-meta-{task_id} {{
                        display: flex;
                        justify-content: space-between;
                        font-size: 0.8em;
                    }}
                    .priority-badge-{task_id} {{
                        background-color: {priority_color}33;
                        color: {priority_color};
                        padding: 2px 6px;
                        border-radius: 10px;
                        font-size: 0.7em;
                    }}
                </style>
                """, unsafe_allow_html=True)
                
                # Create the task card with HTML
                due_status = get_due_status(task.get('due_date', ''))
                due_color = "red" if due_status == "overdue" else "orange" if due_status == "due-soon" else "white"
                
                st.markdown(f"""
                <div class="task-card-{task_id}">
                    <div class="task-title-{task_id}">{task.get('title', 'No Title')}</div>
                    <div class="task-desc-{task_id}">{task.get('description', '')[:50] + ('...' if len(task.get('description', '')) > 50 else '')}</div>
                    <div class="task-meta-{task_id}">
                        <span style="color: {due_color}">Due: {task.get('due_date', 'N/A')}</span>
                        <span class="priority-badge-{task_id}">{task.get('priority', 'Medium')}</span>
                    </div>
                    <div style="font-size: 0.8em; margin-top: 5px;">{task.get('assignee', '')}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Add action buttons below the card
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("⬅️ Back", key=f"back_{task_id}"):
                        update_task_status(task_id, "To Do")
                        st.success(f"Task '{task.get('title')}' moved back to To Do")
                        time.sleep(0.5)
                        st.rerun()
                        
                with col2:
                    if st.button("✏️ Edit", key=f"edit_{task_id}"):
                        st.session_state.selected_task_id = task_id
                        st.session_state.show_task_form = True
                        st.rerun()
                        
                with col3:
                    if st.button("✅ Done", key=f"done_{task_id}"):
                        update_task_status(task_id, "Done")
                        st.success(f"Task '{task.get('title')}' moved to Done")
                        time.sleep(0.5)
                        st.rerun()
    
    # Render Done column
    with done_col:
        # Add a button to archive all done tasks
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### Done ({len(done_tasks)})")
        with col2:
            if len(done_tasks) > 0:
                if st.button("🗄️ Archive All"):
                    clear_done_tasks()
                    st.success("All done tasks archived")
                    time.sleep(0.5)
                    st.rerun()
        
        for task in done_tasks:
            task_id = task.get('id', '')
            with st.container():
                # Create a box with colored left border based on priority
                priority_color = get_priority_color(task.get('priority', 'Medium'))
                
                # Create CSS for the task card
                st.markdown(f"""
                <style>
                    .task-card-{task_id} {{
                        border-left: 4px solid {priority_color};
                        padding: 10px;
                        border-radius: 5px;
                        background-color: #2a2a3c;
                        margin-bottom: 10px;
                        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                    }}
                    .task-title-{task_id} {{
                        font-weight: bold;
                        margin-bottom: 5px;
                    }}
                    .task-desc-{task_id} {{
                        font-size: 0.9em;
                        color: #a1a8c9;
                        margin-bottom: 5px;
                    }}
                    .task-meta-{task_id} {{
                        display: flex;
                        justify-content: space-between;
                        font-size: 0.8em;
                    }}
                    .priority-badge-{task_id} {{
                        background-color: {priority_color}33;
                        color: {priority_color};
                        padding: 2px 6px;
                        border-radius: 10px;
                        font-size: 0.7em;
                    }}
                </style>
                """, unsafe_allow_html=True)
                
                # Create the task card with HTML
                due_status = get_due_status(task.get('due_date', ''))
                due_color = "red" if due_status == "overdue" else "orange" if due_status == "due-soon" else "white"
                
                st.markdown(f"""
                <div class="task-card-{task_id}">
                    <div class="task-title-{task_id}">{task.get('title', 'No Title')}</div>
                    <div class="task-desc-{task_id}">{task.get('description', '')[:50] + ('...' if len(task.get('description', '')) > 50 else '')}</div>
                    <div class="task-meta-{task_id}">
                        <span style="color: {due_color}">Due: {task.get('due_date', 'N/A')}</span>
                        <span class="priority-badge-{task_id}">{task.get('priority', 'Medium')}</span>
                    </div>
                    <div style="font-size: 0.8em; margin-top: 5px;">{task.get('assignee', '')}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Add action buttons below the card
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("⬅️ Back", key=f"back_{task_id}"):
                        update_task_status(task_id, "In Progress")
                        st.success(f"Task '{task.get('title')}' moved back to In Progress")
                        time.sleep(0.5)
                        st.rerun()
                        
                with col2:
                    if st.button("✏️ Edit", key=f"edit_{task_id}"):
                        st.session_state.selected_task_id = task_id
                        st.session_state.show_task_form = True
                        st.rerun()
                        
                with col3:
                    if st.button("🗄️ Archive", key=f"archive_{task_id}"):
                        delete_task(task_id)
                        st.success(f"Task '{task.get('title')}' archived")
                        time.sleep(0.5)
                        st.rerun()

with sidebar_col:
    # Sidebar for task management
    st.sidebar.title("Task Management")
    
    # Action buttons
    if st.sidebar.button("Create New Task"):
        st.session_state.show_task_form = True
        st.session_state.selected_task_id = None
    
    # Task form
    if st.session_state.show_task_form or st.session_state.selected_task_id is not None:
        with st.sidebar.form("task_form"):
            tasks_df = load_tasks()
            
            # If editing, get the task data
            task_data = {}
            is_editing = False
            
            if st.session_state.selected_task_id is not None:
                is_editing = True
                if 'id' in tasks_df.columns:
                    task_data = tasks_df[tasks_df['id'] == st.session_state.selected_task_id].iloc[0].to_dict()
            
            # Form fields
            st.subheader("Task Details")
            
            title = st.text_input("Title", value=task_data.get('title', ''))
            description = st.text_area("Description", value=task_data.get('description', ''))
            
            col1, col2 = st.columns(2)
            with col1:
                status = st.selectbox(
                    "Status",
                    options=["To Do", "In Progress", "Done"],
                    index=["To Do", "In Progress", "Done"].index(task_data.get('status', 'To Do')) if 'status' in task_data else 0
                )
            with col2:
                priority = st.selectbox(
                    "Priority",
                    options=["Low", "Medium", "High"],
                    index=["Low", "Medium", "High"].index(task_data.get('priority', 'Medium')) if 'priority' in task_data else 1
                )
            
            due_date = st.date_input(
                "Due Date",
                value=datetime.strptime(task_data.get('due_date', datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d") if 'due_date' in task_data else datetime.now()
            )
            
            assignee = st.text_input("Assignee", value=task_data.get('assignee', ''))
            
            # Submit buttons
            if is_editing:
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Update Task"):
                        if update_task(
                            st.session_state.selected_task_id,
                            title,
                            description,
                            status,
                            due_date.strftime("%Y-%m-%d"),
                            priority,
                            assignee
                        ):
                            st.success("Task updated successfully!")
                            st.session_state.show_task_form = False
                            st.session_state.selected_task_id = None
                            time.sleep(0.5)
                            st.rerun()
                
                with col2:
                    if st.form_submit_button("Archive Task"):
                        if delete_task(st.session_state.selected_task_id):
                            st.success("Task archived successfully!")
                            st.session_state.show_task_form = False
                            st.session_state.selected_task_id = None
                            time.sleep(0.5)
                            st.rerun()
            else:
                if st.form_submit_button("Add Task"):
                    if create_task(
                        title,
                        description,
                        status,
                        due_date.strftime("%Y-%m-%d"),
                        priority,
                        assignee
                    ):
                        st.success("Task added successfully!")
                        st.session_state.show_task_form = False
                        time.sleep(0.5)
                        st.rerun()
    
    # Stats and metrics
    st.sidebar.title("Task Statistics")
    
    # Calculate stats
    tasks_df = load_tasks()
    total_tasks = len(tasks_df)
    completed_tasks = len(tasks_df[tasks_df['status'] == 'Done'])
    in_progress_tasks = len(tasks_df[tasks_df['status'] == 'In Progress'])
    todo_tasks = len(tasks_df[tasks_df['status'] == 'To Do'])
    
    completion_rate = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
    
    # Display stats
    st.sidebar.metric("Total Tasks", total_tasks)
    st.sidebar.metric("Completion Rate", f"{completion_rate}%")
    
    # Status breakdown
    st.sidebar.subheader("Status Breakdown")
    status_data = {
        'Status': ['To Do', 'In Progress', 'Done'],
        'Count': [todo_tasks, in_progress_tasks, completed_tasks]
    }
    st.sidebar.bar_chart(pd.DataFrame(status_data).set_index('Status'))
    
    # Priority breakdown
    if 'priority' in tasks_df.columns:
        st.sidebar.subheader("Priority Breakdown")
        priority_counts = tasks_df['priority'].value_counts().reset_index()
        priority_counts.columns = ['Priority', 'Count']
        st.sidebar.bar_chart(priority_counts.set_index('Priority'))
    
    # Admin section for archived tasks
    st.sidebar.title("Admin")
    
    with st.sidebar.expander("Archived Tasks"):
        archived_tasks = load_tasks(include_archived=True)
        archived_tasks = archived_tasks[archived_tasks['archived'] == True]
        if len(archived_tasks) > 0:
            st.write(f"You have {len(archived_tasks)} archived tasks.")
            
            # Option to restore an archived task
            if st.button("Restore All Archived Tasks"):
                # Unarchive all archived tasks
                restore_all_archived_tasks()
                st.success("All tasks restored!")
                time.sleep(0.5)
                st.rerun()
        else:
            st.write("No archived tasks.")
    
    # CSV File Diagnostics
    with st.sidebar.expander("CSV Diagnostics"):
        st.write("### CSV File Information")
        
        # Check if the file exists
        if os.path.exists(DATA_PATH):
            file_size = os.path.getsize(DATA_PATH)
            st.write(f"- CSV File exists: ✅")
            st.write(f"- File size: {file_size} bytes")
            
            # Try to read the file
            try:
                csv_df = pd.read_csv(DATA_PATH)
                st.write(f"- CSV is readable: ✅")
                st.write(f"- Row count: {len(csv_df)}")
                st.write(f"- Column count: {len(csv_df.columns)}")
                
                # Show the first few rows
                st.write("### CSV Preview (First 3 rows)")
                st.dataframe(csv_df.head(3))
                
                # Show column info
                st.write("### Column Information")
                for col in csv_df.columns:
                    st.write(f"- {col}: {csv_df[col].dtype}")
            except Exception as e:
                st.error(f"Error reading CSV: {e}")
        else:
            st.error("CSV file does not exist!")
            
        # Add a rebuild button
        if st.button("🔄 Rebuild CSV File"):
            with st.spinner("Rebuilding CSV file..."):
                try:
                    # Get all tasks from memory
                    tasks_df = load_tasks(include_archived=True)
                    
                    # Create a temp file path
                    temp_path = DATA_PATH + ".new"
                    
                    # Write to temp file
                    tasks_df.to_csv(temp_path, index=False, encoding='utf-8')
                    
                    # Verify temp file
                    test_df = pd.read_csv(temp_path)
                    
                    # Move to main file
                    import shutil
                    if os.path.exists(DATA_PATH):
                        shutil.copy2(DATA_PATH, DATA_PATH + ".backup")
                    shutil.move(temp_path, DATA_PATH)
                    
                    st.success("CSV rebuilt successfully!")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Rebuild failed: {e}")

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #45475a;">
    <p style="color: #a1a8c9; font-size: 0.8rem;">Professional Kanban Board | &copy; 2025</p>
</div>
""", unsafe_allow_html=True)

# Add some basic styling
st.markdown("""
<style>
    /* Dark theme base colors */
    :root {
        --primary-color: #4361ee;
        --success-color: #2dc653;
        --warning-color: #f9c74f;
        --danger-color: #e63946;
        --dark-bg: #1e1e2e;
        --dark-card-bg: #2a2a3c;
        --dark-header-bg: #313244;
        --dark-text: #cdd6f4;
        --dark-text-secondary: #a1a8c9;
        --dark-border: #45475a;
    }
    
    /* Make the board look more like a Kanban board */
    div[data-testid="column"] {
        background-color: var(--dark-card-bg);
        border-radius: 8px;
        padding: 10px;
        margin: 5px;
        border: 1px solid var(--dark-border);
    }
    
    /* Better button styling */
    .stButton button {
        border-radius: 4px;
        font-weight: 500;
        border: none;
        transition: all 0.2s;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Column headers */
    h3 {
        margin-bottom: 15px;
        padding-bottom: 5px;
        border-bottom: 2px solid var(--dark-border);
    }
</style>
""", unsafe_allow_html=True)
