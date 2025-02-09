from flask import Flask, render_template, request, redirect, url_for, session
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session management

genai.configure(api_key="AIzaSyC-PJMrcaRgwL_bxSX7FkREzJu5kcVqlEg")

tasks = ['Buy groceries', 'Complete coding tutorial', 'Walk the dog']

@app.route('/')
def index():
    score = session.get('score', 0)
    return render_template('index.html', tasks=tasks, score=score)

@app.route('/add', methods=['POST'])
def add_task():
    new_task = request.form.get('newTask')
    if new_task:
        tasks.append(new_task)
    return redirect(url_for('index'))

@app.route('/complete', methods=['POST'])
def complete_tasks():
    completed_tasks = request.form.getlist('taskCheckbox')
    score = session.get('score', 0)
    
    for index in map(int, completed_tasks):
        if 1 <= index <= len(tasks) and "Completed" not in tasks[index - 1]:
            tasks[index - 1] += " - Completed"
            score += 1  # Increment score for each completed task
    
    session['score'] = score  # Save score in session
    return redirect(url_for('index'))

@app.route('/game', methods=['GET', 'POST'])
def game():
    score = session.get('score', 0)
    model = genai.GenerativeModel("gemini-pro")
    chat_session = model.start_chat()

    if request.method == 'POST':
        choice = request.form.get('choice', '')
        prompt = f"Continue the adventure based on this choice: {choice}"
    else:
        prompt = "Start a new text-based adventure game. The game must be some what fanatasized describe the avaatar of the person build the person as a weak person first  Describe the scenario and give 2-3 choices."
    
    response = chat_session.send_message(prompt)
    text = response.text

    return render_template('game.html', text=text, score=score)

if __name__ == '__main__':
    
    
    
    app.run(debug=True)
