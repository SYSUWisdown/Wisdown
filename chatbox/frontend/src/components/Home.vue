<template>
  <div>
    <!-- 顶部栏 -->
    <div class="top-bar">
      <div class="spacer"></div>
      <button class="user-btn">{{ username }}</button>
    </div>
    <div class="home-container">
      <!-- 左侧：多人聊天室 -->
      <div class="chat-room">
        <h2>聊天室</h2>
        <div class="messages" ref="messagesContainer">
          <div
            v-for="(msg, idx) in messages"
            :key="idx"
            class="msg"
            :class="{ self: msg.username === username }"
          >
            <span class="avatar">{{ msg.username.slice(0, 1).toUpperCase() }}</span>
            <div class="msg-content">
              <div class="msg-user">{{ msg.username }}</div>
              <div class="msg-bubble">{{ msg.text }}</div>
            </div>
          </div>
        </div>
        <div class="input-bar">
          <input v-model="input" @keyup.enter="send" placeholder="输入消息并回车" />
          <button @click="send">发送</button>
        </div>
      </div>
      <!-- 右侧：Markdown 展示区 -->
      <div class="markdown-editor">
        <h2>Markdown 展示区</h2>
        <!-- <button @click="triggerPythonPush" style="margin-bottom:12px;">
          拉取Python生成内容
        </button> -->
        <div class="md-preview" v-html="renderedHtml"></div>
      </div>
    </div>
  </div>
</template>

<script>
import { io } from "socket.io-client";
import IP from '../../../ipconfig';
import { marked } from "marked";
import axios from 'axios';
export default {
  name: "HomePage",
  data() {
    return {
      socket: null,
      messages: [],
      input: "",
      username: localStorage.getItem("username") || "未登录用户",
      markdownContent: ""
    };
  },
  computed: {
    renderedHtml() {
      return marked.parse(this.markdownContent || '');
    }
  },
  mounted() {
    this.username = localStorage.getItem("username") || "未登录用户";

    // 拉取历史消息
    axios.get(`http://${IP}:3000/api/messages?limit=50`)
      .then(res => {
        res.data.forEach(msg => {
          // 兼容你的消息结构
          this.messages.push({
            username: msg.username,
            text: msg.content,
            time: new Date(msg.created_at).getTime()
          });
        });
        this.$nextTick(() => {
          this.scrollToBottom();
        });
      });

    // socket.io 连接和监听
    this.socket = io(`http://${IP}:3000`);
    this.socket.on("chat message", msg => {
      this.messages.push(msg);
      this.$nextTick(() => {
        this.scrollToBottom();
      });
    });
    // 监听后端推送的 markdown 内容
    this.socket.on("markdown update", content => {
      this.markdownContent = content || '';
    });
  },
  methods: {
    send() {
      if (this.input.trim()) {
        this.socket.emit("chat message", {
          username: this.username,
          text: this.input.trim()
        });
        this.input = "";
        this.$nextTick(() => {
          this.scrollToBottom();
        });
      }
    },
    scrollToBottom() {
      const container = this.$refs.messagesContainer;
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    },
    async triggerPythonPush() {
      try {
        await axios.post(`http://${IP}:3000/push-md-from-python`);
        // 可选：提示用户
        // alert('已请求后端推送最新内容');
      } catch (e) {
        alert('触发失败: ' + (e.response?.data?.error || e.message));
      }
    }
  },
  watch: {
    username(newVal) {
      localStorage.setItem("username", newVal);
    }
  }
};
</script>

<!-- 引入 Editor.md 样式 -->
<style scoped>
.top-bar {
  width: 100vw;
  height: 48px;
  background: #6db5cb;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0 32px;
  box-sizing: border-box;
  border-bottom: 1px solid #eee;
}
.spacer {
  flex: 1;
}
.user-btn {
  background: #f3ae6e;
  border: 1px solid #ddd;
  border-radius: 16px;
  padding: 6px 18px;
  font-size: 15px;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(44,62,80,0.04);
}
.home-container {
  display: flex;
  gap: 0;
  max-width: 100vw;
  height: calc(100vh - 48px);
  min-height: 500px;
  background: #f0f2f5;
}
.chat-room, .markdown-editor {
  flex: 1;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(44, 62, 80, 0.08);
  padding: 24px;
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 90vh;
  margin: 24px;
}
.chat-room {
  margin-right: 12px;
}
.markdown-editor {
  margin-left: 12px;
}
.messages {
  min-height: 200px;
  max-height: 60vh;
  overflow-y: auto;
  margin-bottom: 16px;
  padding: 8px;
  border-radius: 8px;
  background: #fafbfc;
  flex: 1;
}
.msg {
  display: flex;
  align-items: flex-end;
  margin-bottom: 16px;
}
.msg.self {
  flex-direction: row-reverse;
}
.avatar {
  width: 36px;
  height: 36px;
  background: #1890ff;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 18px;
  margin: 0 8px;
}
.msg.self .avatar {
  background: #52c41a;
}
.msg-content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  max-width: 70%;
}
.msg.self .msg-content {
  align-items: flex-end;
}
.msg-user {
  font-size: 12px;
  color: #888;
  margin-bottom: 2px;
}
.msg-bubble {
  font-size: 16px;
  color: #222;
  background: #f5f5f5;
  border-radius: 6px;
  padding: 8px 16px;
  display: inline-block;
  max-width: 100%;
  position: relative;
  word-break: break-word;
}
.msg.self .msg-bubble {
  background: #95ec69;
  color: #222;
}
.msg-bubble.ai {
  background: #e5e5e5;
  color: #222;
}
.input-bar {
  display: flex;
  align-items: center;
  margin-top: 8px;
}
input {
  flex: 1;
  padding: 10px;
  border-radius: 6px;
  border: 1px solid #ddd;
  margin-right: 12px;
  font-size: 15px;
  background: #fafbfc;
  transition: border 0.2s;
}
input:focus {
  border: 1.5px solid #1890ff;
  outline: none;
}
button {
  padding: 10px 24px;
  background: #1890ff;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 15px;
  cursor: pointer;
  transition: background 0.2s;
}
button:hover {
  background: #40a9ff;
}
.markdown-editor {
  flex: 1;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(44, 62, 80, 0.08);
  padding: 24px;
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 90vh;
  margin: 24px;
}

#editor-md {
  flex: 1;
  min-height: 0;
  /* 让编辑器高度自适应填满父容器 */
}
.md-preview {
  flex: 1;
  min-height: 0;
  background: #fafbfc;
  border-radius: 8px;
  padding: 18px;
  overflow-y: auto;
  font-size: 16px;
  color: #222;
  border: 1px solid #eee;
}
</style>