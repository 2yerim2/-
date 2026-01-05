# 핵심
웹 브라우저로 접속하는 게시판.
누구나 쉽게 접근해 글을 작성하고 게시할 수 있는 게시판임. 회사 사내 게시판, 블로그 게시판, 학교 및 학원 게시판 등 다양한 커뮤니티에 응용할 수 있는 게시판임.

# 기능 설명
## 1. 로그인 및 회원가입 기능
- 맨 처음 가입하는 사람은 '회원가입' 기능을 통해 가입할 수 있음. 원하는 아이디와 비밀번호를 입력하여 계정을 생성할 수 있고, 브라우저가 이 암호를 기억하여 자동 로그인 가능함. Flask의 flash 기능 이용.
```
from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from datetime import datetime
from functools import wraps
```
```@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        if password != password_confirm:
            flash('비밀번호가 일치하지 않습니다.')
            return render_template('register.html')
        
        users = read_json(USERS_FILE)
        
        # 중복 체크
        if any(u['username'] == username for u in users):
            flash('이미 존재하는 사용자명입니다.')
            return render_template('register.html')
        
        # 새 사용자 추가
        new_user = {
            'id': len(users) + 1,
            'username': username,
            'password': password
        }
        users.append(new_user) #추가
        write_json(USERS_FILE, users)
        
        flash('회원가입이 완료되었습니다. 로그인해주세요.')
        return redirect(url_for('login'))
    
    return render_template('register.html')
```
### 로그인 및 로그아웃
```@app.route('/login', methods=['GET', 'POST'])
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
```
```
@app.route('/logout')
def logout():
    session.clear()
    flash('로그아웃되었습니다.')
    return redirect(url_for('login'))
```


## 2. 게시글 목록
- 각자가 글을 작성하면 게시글 목록에 시간 순서대로 기록되어짐. 이 게시판 앱에 가입한 모든 사람은 게시글 목록에 있는 모든 글들을 확인할 수 있음. 오른쪽 상단에 로그아웃 버튼이 있고 , 그 밑에는 '새 게시글 작성' 버튼이 있음. 이 버튼을 통해 사용자는 새로운 글을 작성할 수 있음.
```
@app.route('/board')
@login_required
def board():
    posts = read_json(POSTS_FILE)
    # 최신순으로 정렬
    posts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return render_template('board.html', posts=posts)
```

## 3. 새 게시글 작성
- 새 게시글 작성 버튼을 눌러 작성자가 원하는 제목과 글을 작성하여 게시할 수 있음. 작성자는 익명 또는 실명 중 하나를 선택하여 글을 게시할 수 있음.
```
@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST': #정보 보내기
        title = request.form.get('title')
        content = request.form.get('content')
        is_anonymous = request.form.get('is_anonymous') == 'true'
        
        if not title or not content:
            flash('제목과 내용을 모두 입력해주세요.')
            return render_template('post_form.html')
        
        posts = read_json(POSTS_FILE)
        # 익명 선택 시 표시할 작성자명 결정
        display_author = '익명' if is_anonymous else session['username']
        
        new_post = {
            'id': len(posts) + 1,
            'title': title,
            'content': content,
            'author': session['username'],  # 실제 작성자 (수정 권한 확인용)
            'display_author': display_author,  # 표시할 작성자명(익명 또는 실명)
            'is_anonymous': is_anonymous, (Ture 또는 False의 값을 가짐)
            'author_id': session['user_id'],
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        posts.append(new_post)
        write_json(POSTS_FILE, posts)
        
        flash('게시글이 작성되었습니다.')
        return redirect(url_for('board')) #보드 게시판으로 다시 이동
    
    return render_template('post_form.html')
```
### 게시글 수정
```
@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    posts = read_json(POSTS_FILE)
    post = next((p for p in posts if p['id'] == post_id), None)
    
    if not post:
        flash('게시글을 찾을 수 없습니다.')
        return redirect(url_for('board'))
    
    # 작성자만 수정 가능
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
```

# 부연 설명
- '게시판' 글씨 앞쪽과 목록, 번호 등의 글씨에 맞는 이모티콘을 추가하여 미관상으로 예쁘게 꾸미고 사용자들이 편하고 쉽게 접근할 수 있도록 만들었음.
- 게시판 글을 작성할 때 익명/실명 선택 작성을 가능하게 하여 실제 웹 게시판으로 응용 가능하게 만들었음.
=======
# Flask 게시판

Python Flask를 사용한 간단한 게시판 애플리케이션.

## 기능

- 회원가입 및 로그인
- 게시글 목록 조회 (테이블 형식)
- 게시글 작성
- 게시글 상세보기
- 게시글 수정 (작성자만 가능)
- 데이터는 JSON 파일로 저장

## 설치 및 실행

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. 애플리케이션 실행:
```bash
python app.py
```

3. 브라우저에서 접속:
```
http://localhost:5000
```

## 사용 방법

1. 회원가입: `/register`에서 새 계정 생성
2. 로그인: `/login`에서 로그인
3. 게시판: 로그인 후 게시글 목록 확인
4. 게시글 작성: "새 게시글 작성" 버튼 클릭
5. 게시글 상세보기: 게시글 제목 클릭
6. 게시글 수정: 상세보기 페이지에서 "수정" 버튼 클릭 (작성자만 가능)

## 데이터 저장

- 사용자 정보: `data/users.json`
- 게시글 정보: `data/posts.json`

## 주의사항

- 프로덕션 환경에서는 `app.secret_key`를 변경해야 함.
- 현재는 비밀번호가 평문으로 저장됨. 실제 서비스에서는 해시화가 필요함.
