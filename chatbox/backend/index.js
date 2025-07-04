import Database from 'better-sqlite3';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import axios from 'axios';
import express from 'express';
import http from 'http';
import { Server } from 'socket.io';
import fs from 'fs';
import cors from 'cors';
import IP from '../ipconfig.js';
// 其他依赖同理

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dbPath = path.join(__dirname, 'chat.db');
const db = new Database(dbPath);

// 初始化表
db.exec(`
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  is_admin INTEGER DEFAULT 0,  -- 新增管理员字段
  is_ai INTEGER DEFAULT 0,  -- 新增AI用户字段
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  username TEXT NOT NULL,
  name TEXT NOT NULL,  -- 新增消息名称字段
  content TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS md_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  username TEXT NOT NULL,
  name TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ima_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  username TEXT NOT NULL,
  name TEXT NOT NULL,  -- 新增消息名称字段
  content TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
`);

db.exec('DELETE FROM users;');
db.exec('DELETE FROM messages;');
db.exec('DELETE FROM md_messages;');
db.exec('DELETE FROM ima_messages;');

const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: '*' } });

app.use(express.json());
app.use(cors());

// 添加admin用户
db.prepare('INSERT INTO users (username, password_hash, is_admin, is_ai) VALUES (?, ?, ?, ?)').run('admin', '123456', 1, 0);

// 新增3条测试用的md消息
db.prepare('INSERT INTO md_messages (user_id, username, name, content) VALUES (?, ?, ?, ?)')
  .run(1, 'admin', 'test1.md', '# 测试MD文件1\n这是第一个测试内容 \n 666 \n \n 666 \n\n 666 \n\n 666 \n\n 666 \n\n 666 \n\n 666 \n\n 666 \n\n 999 \n\n 666 \n\n 666 \n\n 666 \n\n 666 \n\n 666 \n\n 666 \n\n 666 \n\n 666 \n\n 666 \n\n 888 \n\n\n 777');
db.prepare('INSERT INTO md_messages (user_id, username, name, content) VALUES (?, ?, ?, ?)')
  .run(1, 'admin', 'test2.md', '# 测试MD文件2\n这是第二个测试内容');
db.prepare('INSERT INTO md_messages (user_id, username, name, content) VALUES (?, ?, ?, ?)')
  .run(1, 'admin', 'test3.md', '# 测试MD文件3\n这是第三个测试内容');

// db.prepare('INSERT INTO ima_messages (user_id, username, name, content) VALUES (?, ?, ?, ?)')
//   .run(1, 'admin', 'test1.uml', '# 测试MD文件2\n这是第二个测试内容');
// db.prepare('INSERT INTO ima_messages (user_id, username, name, content) VALUES (?, ?, ?, ?)')
//   .run(1, 'admin', 'test3.uml', '# 测试MD文件3\n这是第三个测试内容');

// 注册接口
app.post('/register', (req, res) => {
  const { username, password } = req.body;
  try {
    // 普通用户注册，is_admin=0, is_ai=0
    db.prepare(
      'INSERT INTO users (username, password_hash, is_admin, is_ai) VALUES (?, ?, 0, 0)'
    ).run(username, password);

    const users = db.prepare('SELECT username FROM users').all();
    console.log('当前已注册用户:', users.map(u => u.username));

    res.status(200).send('注册成功');
  } catch (e) {
    if (e.code === 'SQLITE_CONSTRAINT_UNIQUE') {
      res.status(400).json({ message: '用户名已存在' });
    } else {
      res.status(500).json({ message: '注册失败' });
    }
  }
});

// 登录接口
app.post('/login', (req, res) => {
  const { username, password } = req.body;
  const user = db.prepare(
    'SELECT * FROM users WHERE username = ? AND password_hash = ?'
  ).get(username, password);
  if (user) {
    res.status(200).json({ message: '登录成功', username: user.username });
  } else {
    res.status(401).json({ message: '用户名或密码错误' });
  }
});

// 获取历史消息接口
app.get('/api/messages', (req, res) => {
  const limit = parseInt(req.query.limit) || 20;
  const rows = db.prepare('SELECT * FROM messages ORDER BY id DESC LIMIT ?').all(limit);
  // 按时间正序返回
  res.json(rows.reverse());
});

app.get('/api/md_messages', (req, res) => {
  const limit = parseInt(req.query.limit) || 20;
  const rows = db.prepare('SELECT * FROM md_messages ORDER BY id DESC LIMIT ?').all(limit);
  // 按时间正序返回
  res.json(rows.reverse());
});

app.get('/api/uml_messages', (req, res) => {
  const limit = parseInt(req.query.limit) || 20;
  const rows = db.prepare('SELECT * FROM ima_messages ORDER BY id DESC LIMIT ?').all(limit);
  // 按时间正序返回
  res.json(rows.reverse());
});

// 聊天室 Socket.IO
io.on('connection', (socket) => {
  console.log('新用户连接:', socket.id);

  socket.on('chat message', (msg) => {
    const messageObj = {
      username: msg.username,
      name: msg.name || 'chat', // 新增消息名称
      text: msg.text,
      time: Date.now()
    };
    io.emit('chat message', messageObj);

    // 存储到数据库
    try {
      const userRow = db.prepare('SELECT id FROM users WHERE username = ?').get(msg.username);
      const userId = userRow ? userRow.id : 0;
      db.prepare(
        'INSERT INTO messages (user_id, username, name, content) VALUES (?, ?, ?, ?)'
      ).run(userId, msg.username, messageObj.name, msg.text);
    } catch (e) {
      console.error('消息存储失败:', e.message);
    }
  });

  socket.on('disconnect', () => {
    console.log('用户断开:', socket.id);
  });

  // ② 前端请求修改某md文件内容
  socket.on('write md', ({ name, username, content }) => {
    try {
      // 获取用户id
      const userRow = db.prepare('SELECT id FROM users WHERE username = ?').get(username);
      const userId = userRow ? userRow.id : 0;
      db.prepare(
        'INSERT INTO md_messages (user_id, username, name, content) VALUES (?, ?, ?, ?)'
      ).run(userId, username, name, content);

      // 广播最新内容给所有人（只广播本文件）
      io.emit('markdown update', { name, content });
    } catch (e) {
      socket.emit('md content', { name, error: '数据库写入失败' });
    }
  });
});

const PORT = 3000;
server.listen(PORT, '0.0.0.0', () => {
  console.log(`服务器运行在 http://${IP}:${PORT}`);
});

let lastMdFiles = [];
let lastUmlFiles = [];

// 定时检测数据库中md文件名变化
setInterval(() => {
  const rows = db.prepare(
    `SELECT name, content, MAX(created_at) as last_time
     FROM md_messages
     GROUP BY name
     ORDER BY last_time DESC
     LIMIT 5`
  ).all();
  const mdList = rows.map(row => [row.name, row.content]);
  const lastNames = lastMdFiles.map(item => item[0]);
  const currNames = mdList.map(item => item[0]);
  if (
    currNames.length !== lastNames.length ||
    currNames.some((n, i) => n !== lastNames[i])
  ) {
    mdList.forEach(([name, content]) => {
      io.emit('add md item', { name, content });
    });
    lastMdFiles = mdList;
  }

  const umlRows = db.prepare(
    `SELECT name, content, MAX(created_at) as last_time
     FROM ima_messages
     GROUP BY name
     ORDER BY last_time DESC
     LIMIT 5`
  ).all();
  const umlList = umlRows.map(row => [row.name, row.content]);
  const lastUmlNames = lastUmlFiles.map(item => item[0]);
  const currUmlNames = umlList.map(item => item[0]);
  if (
    currUmlNames.length !== lastUmlNames.length ||
    currUmlNames.some((n, i) => n !== lastUmlNames[i])
  ) {
    console.log('检测到UML文件变化:', umlList);
    umlList.forEach(([name, content]) => {
      io.emit('add uml item', { name, content });
    });
    lastUmlFiles = umlList;
  }
}, 500);