from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
import urllib.parse as up

app = Flask(__name__)
CORS(app)  # 允许前端跨域请求

# --- 1. 从环境变量获取数据库连接字符串 ---
database_url = os.environ.get('DATABASE_URL')

# 如果DATABASE_URL是以postgres://开头的旧格式，Vercel/某些库可能需要postgresql://
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

# --- 2. 创建数据库连接函数 ---
def get_db_connection():
    """
    连接到Supabase PostgreSQL数据库
    """
    if not database_url:
        raise ValueError("DATABASE_URL 环境变量未设置！")
    
    # 解析URL并建立连接
    conn = psycopg2.connect(
        database_url,
        cursor_factory=RealDictCursor  # 使返回的结果为字典格式，更方便处理
    )
    return conn

# --- 3. 初始化数据库表（如果不存在） ---
def init_db():
    """创建用户表（如果不存在）"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 创建users表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ 数据库表初始化/检查完成")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")

# --- 4. 你的API路由 ---
@app.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
        
        # 哈希密码
        password_hash = generate_password_hash(password)
        
        # 保存到数据库
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            'INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id;',
            (username, password_hash)
        )
        
        conn.commit()
        user_id = cur.fetchone()['id']
        
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '注册成功',
            'user_id': user_id
        })
        
    except psycopg2.IntegrityError:
        # 用户名重复
        return jsonify({'success': False, 'message': '用户名已存在'}), 400
    except Exception as e:
        print(f"注册错误: {e}")
        return jsonify({'success': False, 'message': '注册失败，服务器错误'}), 500

@app.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
        
        # 从数据库查询用户
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            'SELECT id, username, password_hash FROM users WHERE username = %s;',
            (username,)
        )
        
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 401
        
        # 验证密码
        if check_password_hash(user['password_hash'], password):
            return jsonify({
                'success': True,
                'message': '登录成功',
                'user_id': user['id'],
                'username': user['username']
            })
        else:
            return jsonify({'success': False, 'message': '密码错误'}), 401
            
    except Exception as e:
        print(f"登录错误: {e}")
        return jsonify({'success': False, 'message': '登录失败，服务器错误'}), 500

# 测试用根路由
@app.route('/')
def home():
    return jsonify({
        'message': 'Flask后端运行正常！',
        'status': '在线',
        'database_configured': bool(database_url)  # 检查数据库配置
    })

# --- 5. 初始化并运行（仅当直接执行时） ---
if __name__ == '__main__':
    print("正在初始化数据库...")
    init_db()
    app.run(debug=True)
else:
    # 在Vercel的Serverless环境中，也需要确保表存在
    init_db()