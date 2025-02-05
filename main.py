from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

tasks = ['']
score = 0 

@app.route('/')
def index():
    return render_template('index.html', tasks=tasks, score=score)  



@app.route('/add', methods=['POST'])
def add_task():
    new_task = request.form.get('newTask')
    if new_task:
        tasks.append(new_task)
    return redirect(url_for('index'))



@app.route('/complete', methods=['POST'])
def complete_tasks():
    global score  
    completed_tasks = request.form.getlist('taskCheckbox')
    
    for index in map(int, completed_tasks):
        if 1 <= index <= len(tasks) and "Completed" not in tasks[index - 1]:
            tasks[index - 1] += " - Completed"
            score += 1  
    
    return redirect(url_for('index'))



if __name__ == '__main__':
    app.run(debug=True)
