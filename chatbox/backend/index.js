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
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  username TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
`);

const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: '*' } });

// 用于控制轮询频率
let lastPollTime = 0;
const messageTimes = [];
const POLL_INTERVAL = 30 * 1000; // 高频聊天下的轮询间隔
const MSG_WINDOW_MS = 60 * 1000; // 统计消息频率的时间窗口
const HIGH_FREQ_COUNT = 5; // 一分钟消息数超过该值视为高频

async function pollLLM() {
  try {
    const pyRes = await axios.post('http://localhost:8001/chat', { action: 'chat' });
    const { output_path } = pyRes.data;
    if (output_path) {
      const content = fs.readFileSync(output_path, 'utf-8');
      io.emit('markdown update', content);
      lastPollTime = Date.now();
      return;
    }
    throw new Error('no output');
  } catch (e) {
    try {
      const listRes = await axios.post('http://localhost:8001/chat', { action: 'list' });
      const files = listRes.data.files || [];
      if (files.length) {
        files.sort((a, b) => {
          const ta = parseInt(a.match(/_(\d+)\./)?.[1] || 0);
          const tb = parseInt(b.match(/_(\d+)\./)?.[1] || 0);
          return tb - ta;
        });
        const latest = files[0];
        const outputPath = `/app/plugin_outputs/${latest}`;
        const content = fs.readFileSync(outputPath, 'utf-8');
        io.emit('markdown update', content);
        lastPollTime = Date.now();
      }
    } catch (err) {
      console.error('轮询失败:', err.message);
    }
  }
}

function handlePolling() {
  const now = Date.now();
  messageTimes.push(now);
  while (messageTimes.length && now - messageTimes[0] > MSG_WINDOW_MS) {
    messageTimes.shift();
  }
  const highFreq = messageTimes.length > HIGH_FREQ_COUNT;
  if (highFreq) {
    if (now - lastPollTime >= POLL_INTERVAL) {
      pollLLM();
    }
  } else {
    pollLLM();
  }
}

app.use(express.json());
app.use(cors());

// 注册接口
app.post('/register', (req, res) => {
  const { username, password } = req.body;
  try {
    db.prepare(
      'INSERT INTO users (username, password_hash) VALUES (?, ?)'
    ).run(username, password); // 实际项目应加密密码
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

// 提供一个接口触发推送
app.post('/push-md-from-python', async (req, res) => {
  try {
    // 1. 调用 Python 服务
    const pyRes = await axios.post('http://localhost:8001/chat', { action: 'chat' });
    const { output_path } = pyRes.data;

    // 2. 读取 markdown 文件内容
    const mdContent = fs.readFileSync(output_path, 'utf-8');

    // 3. 推送到所有前端
    io.emit('markdown update', mdContent);

    res.json({ status: 'ok', output_path });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});
// app.post('/push-md-from-python', async (req, res) => {
//   try {
//     // 1. 调用 Python 服务
//     const pyRes = await axios.post('http://localhost:8001/chat', { action: 'chat' });
//     // 直接取 reply 字段（或你想显示的字段）
//     const mdContent = pyRes.data.reply || '无内容';

//     // 2. 推送到所有前端
//     io.emit('markdown update', mdContent);

//     res.json({ status: 'ok' });
//   } catch (e) {
//     res.status(500).json({ error: e.message });
//   }
// });

// 获取历史消息接口
app.get('/api/messages', (req, res) => {
  const limit = parseInt(req.query.limit) || 20;
  const rows = db.prepare('SELECT * FROM messages ORDER BY id DESC LIMIT ?').all(limit);
  // 按时间正序返回
  res.json(rows.reverse());
});

// 聊天室 Socket.IO
io.on('connection', (socket) => {
  console.log('新用户连接:', socket.id);

  socket.on('chat message', (msg) => {
    const messageObj = {
      username: msg.username,
      text: msg.text,
      time: Date.now()
    };
    io.emit('chat message', messageObj);

    // 存储到数据库
    try {
      // 查找用户ID（如无则为0）
      const userRow = db.prepare('SELECT id FROM users WHERE username = ?').get(msg.username);
      const userId = userRow ? userRow.id : 0;
      db.prepare(
        'INSERT INTO messages (user_id, username, content) VALUES (?, ?, ?)'
      ).run(userId, msg.username, msg.text);
    } catch (e) {
      console.error('消息存储失败:', e.message);
    }

    // 根据聊天频率执行轮询
    handlePolling();
  });

  socket.on('disconnect', () => {
    console.log('用户断开:', socket.id);
  });
});

const PORT = 3000;
server.listen(PORT, '0.0.0.0', () => {
  console.log(`服务器运行在 http://${IP}:${PORT}`);
});