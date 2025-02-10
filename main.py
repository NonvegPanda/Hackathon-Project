from flask import Flask, render_template, request, redirect, url_for, session
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = "your_secret_key" 
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
def complete():
    global score  
    completed_tasks = request.form.getlist('taskCheckbox')
    
    for i in completed_tasks:
        tasks[int(i)-1] += " - Completed"
        score += 1
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
        prompt = "Start a new text-based adventure game. The game must be some what fanatasized describe the avaatar of the person build the person as a weak person first  Describe the scenario and give 2-3 choices.Please make the scenarios shorter."
    
    response = chat_session.send_message(prompt)
    text = response.text

    return render_template('game.html', text=text, score=score)

if __name__ == '__main__':
    app.run(debug=True)
