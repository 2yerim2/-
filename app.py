from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

DATA_DIR = 'data'
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
POSTS_FILE = os.path.join(DATA_DIR, 'posts.json')

os.makedirs(DATA_DIR, exist_ok=True)

def init_json_file(filepath, default_data):
    if not os.path.exists(filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('로그인이 필요합니다.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def read_json(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def write_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

init_json_file(USERS_FILE, [])
init_json_file(POSTS_FILE, [])

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('board'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        users = read_json(USERS_FILE)
        user = next((u for u in users if u['username'] == username and u['password'] == password), None)
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('로그인 성공!')
            return redirect(url_for('board'))
        else:
            flash('아이디 또는 비밀번호가 올바르지 않습니다.')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        if password != password_confirm:
            flash('비밀번호가 일치하지 않습니다.')
            return render_template('register.html')
        
        users = read_json(USERS_FILE)
        
        if any(u['username'] == username for u in users):
            flash('이미 존재하는 사용자명입니다.')
            return render_template('register.html')
    
        new_user = {
            'id': len(users) + 1,
            'username': username,
            'password': password
        }
        users.append(new_user)
        write_json(USERS_FILE, users)
        
        flash('회원가입이 완료되었습니다. 로그인해주세요.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('로그아웃되었습니다.')
    return redirect(url_for('login'))

@app.route('/board')
@login_required
def board():
    posts = read_json(POSTS_FILE)
    posts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return render_template('board.html', posts=posts)

@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        is_anonymous = request.form.get('is_anonymous') == 'true'
        
        if not title or not content:
            flash('제목과 내용을 모두 입력해주세요.')
            return render_template('post_form.html')
        
        posts = read_json(POSTS_FILE)
        
        display_author = '익명' if is_anonymous else session['username']
        
        new_post = {
            'id': len(posts) + 1,
            'title': title,
            'content': content,
            'author': session['username'], 
            'display_author': display_author,  
            'is_anonymous': is_anonymous,
            'author_id': session['user_id'],
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        posts.append(new_post)
        write_json(POSTS_FILE, posts)
        
        flash('게시글이 작성되었습니다.')
        return redirect(url_for('board'))
    
    return render_template('post_form.html')

@app.route('/post/<int:post_id>')
@login_required
def post_detail(post_id):
    posts = read_json(POSTS_FILE)
    post = next((p for p in posts if p['id'] == post_id), None)
    
    if not post:
        flash('게시글을 찾을 수 없습니다.')
        return redirect(url_for('board'))
    
    return render_template('post_detail.html', post=post)

@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    posts = read_json(POSTS_FILE)
    post = next((p for p in posts if p['id'] == post_id), None)
    
    if not post:
        flash('게시글을 찾을 수 없습니다.')
        return redirect(url_for('board'))
    
    if post['author_id'] != session['user_id']:
        flash('수정 권한이 없습니다.')
        return redirect(url_for('post_detail', post_id=post_id))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        if not title or not content:
            flash('제목과 내용을 모두 입력해주세요.')
            return render_template('post_form.html', post=post)
        
        post['title'] = title
        post['content'] = content
        post['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        write_json(POSTS_FILE, posts)
        flash('게시글이 수정되었습니다.')
        return redirect(url_for('post_detail', post_id=post_id))
    
    return render_template('post_form.html', post=post)

if __name__ == '__main__':
    app.run(debug=True)

