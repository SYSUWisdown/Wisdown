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
          <input v-model="input" @keyup.enter="send_msg" placeholder="输入消息并回车" />
          <button @click="send_msg">发送</button>
        </div>
      </div>
      <!-- 右侧：Markdown 展示区和UML展示区 -->
      <div class="right-section">
        <!-- 上方：Markdown 展示区 -->
        <div class="markdown-editor-with-tabs">
          <div class="md-tabs-vertical">
            <div
              v-for="name in mdFiles"
              :key="name"
              class="md-tab-btn-wrap"
            >
              <button
                :class="['md-tab-btn', { active: name === activeMd }]"
                @click="selectMd(name)"
              >
                {{ name }}
                <span class="close-x" @click.stop="closeMd(name)">×</span>
              </button>
            </div>
          </div>
          <div class="md-preview-area">
            <h2>MarkDown 展示区</h2>
            <div class="md-preview" v-html="renderedHtml"></div>
          </div>
        </div>
        
        <!-- 下方：UML 展示区 -->
        <div class="uml-editor-with-tabs" v-show="showUmlArea">
          <div class="uml-tabs-vertical">
            <div
              v-for="name in umlFiles"
              :key="name"
              class="uml-tab-btn-wrap"
            >
              <button
                :class="['uml-tab-btn', { uml_active: name === activeUml }]"
                @click="selectUml(name)"
              >
                {{ name }}
                <span class="close-x" @click.stop="closeUml(name)">×</span>
              </button>
            </div>
          </div>
          <div class="uml-preview-area">
            <div class="uml-header">
              <h2>UML图 展示区</h2>
              <span class="close-x" @click="closeUmlArea()">×</span>
            </div>
            <div class="uml-preview" v-html="showUML"></div>
          </div>          
        </div>
        
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
      markdownContent: [],
      mdFiles: [],         // 所有md文件名
      activeMd: "",         // 当前激活的md文件名
      umldownContent: [],
      umlFiles: [],         // 所有UML文件名
      activeUml: "",         // 当前激活的UML文件名
      showUmlArea: false
    };
  },
  computed: {
    renderedHtml() {
      // 查找当前激活md文件的内容
      const md = this.markdownContent.find(item => item.name === this.activeMd);
      return marked.parse(md ? md.content : '');
      //return md ? md.content : ''
    },
    showUML() {
      // 查找当前激活UML文件的内容
      const uml = this.umldownContent.find(item => item.name === this.activeUml);
      return uml ? uml.content : '';
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

    axios.get(`http://${IP}:3000/api/md_messages?limit=5`)
      .then(res => {
        res.data.forEach(md => {
          this.markdownContent.push({
            name: md.name,
            content: md.content
          });
          this.mdFiles.push(md.name); // 收集所有md文件名
        });
      });

    axios.get(`http://${IP}:3000/api/uml_messages?limit=5`)
      .then(res => {
        res.data.forEach(uml => {
          this.umldownContent.push({
            name: uml.name,
            content: uml.content
          });
          this.umlFiles.push(uml.name); // 收集所有md文件名
        });
        this.showUmlArea = true;
      });

    // socket.io 连接和监听
    this.socket = io(`http://${IP}:3000`);
    this.socket.on("chat message", msg => {
      this.messages.push(msg);
      this.$nextTick(() => {
        this.scrollToBottom();
      });
    });

    this.socket.on("add md item", ({ name, content }) => {
      // 如果已存在则不重复添加
      if (!this.mdFiles.includes(name)) {
        this.mdFiles.push(name);
        this.markdownContent.push({ name, content });
      }
    });

    this.socket.on("add uml item", ({ name, content }) => {
      // 如果已存在则不重复添加
      if (!this.umlFiles.includes(name)) {
        this.umlFiles.push(name);
        this.umldownContent.push({ name, content });
        this.showUmlArea = true;
      }
    });
  },
  methods: {
    send_msg() {
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
    selectMd(name) {
      this.activeMd = name;
    },
    closeMd(name) {
      // 删除mdFiles和markdownContent中的对应项
      this.mdFiles = this.mdFiles.filter(n => n !== name);
      this.markdownContent = this.markdownContent.filter(md => md.name !== name);
      // 如果当前关闭的是激活的标签，切换到下一个或前一个
      if (this.activeMd === name) {
        if (this.mdFiles.length > 0) {
          this.activeMd = this.mdFiles[0];
        } else {
          this.activeMd = "";
        }
      }
    },
    selectUml(name) {
      this.activeUml = name;
    },
    closeUml(name) {
      // 删除umlFiles和umldownContent中的对应项
      this.umlFiles = this.umlFiles.filter(n => n !== name);
      this.umldownContent = this.umldownContent.filter(uml => uml.name !== name);
      // 如果当前关闭的是激活的标签，切换到下一个或前一个
      if (this.activeUml === name) {
        if (this.umlFiles.length > 0) {   
          this.activeUml = this.umlFiles[0];
        } else {
          this.activeUml = "";
        }
      }
    },
    closeUmlArea() {
      this.showUmlArea = false;
      this.activeUml = "";
      this.umldownContent = [];
      this.umlFiles = [];
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
.chat-room, .right-section {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(44, 62, 80, 0.08);
  padding: 24px;
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 88vh;
  margin: 24px; /* 修改这里：上下24px，左右12px */
}
.chat-room {
  margin-right: 12px;
  display: flex; 
  flex-direction: column;
  gap: 12px;
  flex: 1;
}
.right-section {
  margin-left: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 2;
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

/* Markdown 编辑器样式 */
.markdown-editor-with-tabs {
  display: flex;
  flex: 1;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(44, 62, 80, 0.08);
  min-width: 0;
  height: 50%;
  margin-bottom: 12px;
  overflow: hidden;
}

.md-tabs-vertical {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 120px;
  background: #f6faff;
  border-right: 1px solid #e6e6e6;
  padding: 24px 8px 24px 16px;
  border-radius: 12px 0 0 12px;
  align-items: flex-start;
}

.md-tab-btn {
  width: 100%;
  padding: 8px 12px;
  border: none;
  background: #e6f7ff;
  color: #222;
  border-radius: 6px;
  cursor: pointer;
  font-size: 15px;
  text-align: left;
  transition: background 0.2s;
  margin-bottom: 4px;
}
.md-tab-btn.active {
  background: #1890ff;
  color: #fff;
  font-weight: bold;
}

.md-preview-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 24px;
  min-width: 0;
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

.md-tab-btn-wrap {
  width: 100%;
  position: relative;
}
.md-tab-btn {
  width: 100%;
  padding-right: 28px; /* 给叉号留空间 */
  position: relative;
}
.close-x {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  color: #888;
  font-size: 16px;
  cursor: pointer;
  padding: 0 4px;
  border-radius: 50%;
  transition: background 0.2s, color 0.2s;
}
.close-x:hover {
  background: #f66;
  color: #fff;
}

/* UML 展示区样式 */
.uml-editor-with-tabs {
  display: flex;
  flex: 1;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(44, 62, 80, 0.08);
  min-width: 0;
  height: 50%;
  margin-bottom: 12px;
  overflow: hidden;
}

.uml-tabs-vertical {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 120px;
  background: #f6faff;
  border-right: 1px solid #e6e6e6;
  padding: 24px 8px 24px 16px;
  border-radius: 12px 0 0 12px;
  align-items: flex-start;
}

.uml-preview-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 24px;
  min-width: 0;
}

.uml-tab-btn {
  width: 100%;
  padding: 8px 12px;
  border: none;
  background: #e6f7ff;
  color: #222;
  border-radius: 6px;
  cursor: pointer;
  font-size: 15px;
  text-align: left;
  transition: background 0.2s;
  margin-bottom: 4px;
}
.uml-tab-btn.uml_active {
  background: #1890ff;
  color: #fff;
  font-weight: bold;
}

.uml-tab-btn-wrap {
  width: 100%;
  position: relative;
}
.uml-tab-btn {
  width: 100%;
  padding-right: 28px; /* 给叉号留空间 */
  position: relative;
}

.uml-preview {
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

.uml-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
</style>