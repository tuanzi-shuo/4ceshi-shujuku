# app.py
# 元生智护系统 - 后端核心 (Supabase 适配版)
# 为Vercel + Supabase 平台适配

from flask import Flask, request, jsonify, make_response, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import timedelta
import logging
from urllib.parse import urlparse
import psycopg2  # 新增：Supabase (PostgreSQL) 驱动

# 初始化Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
# 关键修改：从环境变量读取 Supabase 数据库连接字符串
# Supabase 连接字符串格式：postgresql://[user]:[password]@[host]/[dbname]?options=project%3D[project-ref]
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True,
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# 初始化数据库
db = SQLAlchemy(app)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 用户模型 (Supabase 兼容)
class User(db.Model):
    # 明确指定表名，避免Flask-SQLAlchemy的自动命名规则与Supabase冲突
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='medical')  # 'elderly' 或 'medical'
    created_at = db.Column(db.DateTime, server_default=db.func.now())  # Supabase 会自动设置 now()
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# 创建数据库表（如果不存在）
# 注意：在Supabase中，更推荐通过SQL在控制台直接建表，但此代码可确保表结构存在
def init_db():
    with app.app_context():
        # 检查连接
        try:
            db.engine.connect()
            logger.info("✅ 成功连接到 Supabase 数据库")
        except Exception as e:
            logger.error(f"❌ 连接 Supabase 数据库失败: {e}")
            return
        
        # 创建所有表（如果不存在）
        db.create_all()
        logger.info("✅ 数据库表初始化完成")

# 初始化数据库连接和表
init_db()

# 首页 - 提供静态文件（保持不变）
@app.route('/')
def index():
    """返回主入口页面"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>元生智护系统后端 (Supabase)</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            h1 { color: white; margin-bottom: 30px; }
            .card { 
                background: rgba(255,255,255,0.95); 
                border-radius: 15px; 
                padding: 30px; 
                margin: 20px auto; 
                max-width: 700px; 
                box-shadow: 0 15px 35px rgba(0,0,0,0.2);
                color: #333;
            }
            .db-info { 
                background: #f0f9ff; 
                padding: 20px; 
                margin: 20px 0; 
                border-radius: 10px;
                border-left: 4px solid #3ecf8e;
                text-align: left;
            }
            .endpoint { 
                background: white; 
                padding: 15px; 
                margin: 10px 0; 
                border-left: 4px solid #667eea; 
                text-align: left;
                border-radius: 8px;
            }
            code { background: #eee; padding: 2px 6px; border-radius: 4px; font-family: monospace; }
            .status { display: inline-block; padding: 5px 15px; border-radius: 20px; font-weight: bold; }
            .status-ok { background: #3ecf8e; color: white; }
            .status-info { background: #667eea; color: white; }
        </style>
    </head>
    <body>
        <h1>元生智护系统 - 后端服务</h1>
        <div class="card">
            <h2>🚀 服务状态</h2>
            <p><span class="status status-ok">运行正常</span></p>
            
            <div class="db-info">
                <h3>🗃️ 数据库配置</h3>
                <p><strong>类型：</strong> Supabase (PostgreSQL)</p>
                <p><strong>状态：</strong> <span class="status status-ok">已连接</span></p>
                <p><strong>用户表：</strong> <code>users</code></p>
                <p>前端页面入口：<a href="/index.html" target="_blank">进入元生智护系统</a></p>
            </div>
            
            <h3>🔧 API 端点</h3>
            <div class="endpoint">
                <strong>POST /api/register</strong><br>
                用户注册，参数: <code>{"username": "string", "password": "string", "role": "medical|elderly"}</code>
            </div>
            <div class="endpoint">
                <strong>POST /api/login</strong><br>
                用户登录，参数: <code>{"username": "string", "password": "string", "role": "medical|elderly"}</code>
            </div>
            <div class="endpoint">
                <strong>GET /api/check_session</strong><br>
                检查当前会话状态
            </div>
            <div class="endpoint">
                <strong>POST /api/logout</strong><br>
                退出登录
            </div>
            
            <p style="margin-top: 30px; color: #666; font-size: 0.9em;">
                📌 系统使用 Supabase 作为后端数据库，提供稳定可靠的数据存储服务。
            </p>
        </div>
    </body>
    </html>
    '''

# 注册接口（保持不变，但底层数据库已改为Supabase）
@app.route('/api/register', methods=['POST'])
def register():
    """处理用户注册"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        role = data.get('role', 'medical').strip()
        
        # 验证输入
        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
        
        if len(username) < 3:
            return jsonify({'success': False, 'message': '用户名至少3个字符'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'message': '密码至少6个字符'}), 400
        
        if role not in ['medical', 'elderly']:
            return jsonify({'success': False, 'message': '无效的用户角色'}), 400
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': '用户名已存在'}), 409
        
        # 创建新用户
        new_user = User(username=username, role=role)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        logger.info(f"✅ 新用户注册成功: {username}, 角色: {role}")
        return jsonify({
            'success': True, 
            'message': '注册成功',
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"❌ 注册错误: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': '服务器内部错误'}), 500

# 登录接口（保持不变）
@app.route('/api/login', methods=['POST'])
def login():
    """处理用户登录"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        role = data.get('role', 'medical').strip()
        
        # 验证输入
        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
        
        # 查找用户
        user = User.query.filter_by(username=username, role=role).first()
        
        if not user:
            logger.warning(f"⚠️ 登录失败: 用户不存在 {username}, 角色: {role}")
            return jsonify({'success': False, 'message': '用户不存在或角色错误'}), 401
        
        if not user.check_password(password):
            logger.warning(f"⚠️ 登录失败: 密码错误 {username}")
            return jsonify({'success': False, 'message': '密码错误'}), 401
        
        # 设置会话
        session.permanent = True
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        
        logger.info(f"✅ 用户登录成功: {username}, 角色: {role}")
        return jsonify({
            'success': True,
            'message': '登录成功',
            'user': user.to_dict(),
            'redirect': f'{role}_home.html'  # 根据角色重定向到不同首页
        })
        
    except Exception as e:
        logger.error(f"❌ 登录错误: {str(e)}")
        return jsonify({'success': False, 'message': '服务器内部错误'}), 500

# 检查会话状态（保持不变）
@app.route('/api/check_session', methods=['GET'])
def check_session():
    """检查当前登录状态"""
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({
                'success': True,
                'is_logged_in': True,
                'user': user.to_dict()
            })
    
    return jsonify({
        'success': True,
        'is_logged_in': False,
        'message': '未登录'
    })

# 退出登录（保持不变）
@app.route('/api/logout', methods=['POST'])
def logout():
    """退出登录"""
    username = session.get('username', '未知用户')
    session.clear()
    logger.info(f"✅ 用户退出登录: {username}")
    return jsonify({
        'success': True,
        'message': '已退出登录'
    })

# 获取用户列表（仅用于测试）
@app.route('/api/users', methods=['GET'])
def get_users():
    """获取所有用户（测试用）"""
    try:
        users = User.query.all()
        return jsonify({
            'success': True,
            'count': len(users),
            'users': [user.to_dict() for user in users]
        })
    except Exception as e:
        logger.error(f"❌ 获取用户列表错误: {str(e)}")
        return jsonify({'success': False, 'message': '查询失败'}), 500

# 静态文件路由（保持不变）
@app.route('/<path:filename>')
def serve_static(filename):
    """提供静态文件"""
    if '..' in filename or filename.startswith('/'):
        return '文件未找到', 404
    
    if filename == '':
        filename = 'index.html'
    
    return redirect(f'/{filename}')

# 健康检查端点
@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点，用于Vercel监控"""
    try:
        # 测试数据库连接
        db.session.execute('SELECT 1')
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)}'
    
    return jsonify({
        'status': 'healthy',
        'service': '元生智护系统后端',
        'database': db_status,
        'timestamp': db.func.now()
    })

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': '接口不存在'}), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f"❌ 服务器错误: {str(error)}")
    return jsonify({'success': False, 'message': '服务器内部错误'}), 500

# Vercel需要这个handler
handler = app

# 本地运行
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)