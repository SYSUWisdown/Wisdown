<template>
  <div class="container-outer">
    <div class="welcome-title">Welcome to Wisdown</div>
    <div class="container" :class="{ 'right-panel-active': isSignUp }">
      <!-- 登录表单 -->
      <div class="container__form container--signin">
        <form class="form" @submit.prevent="login">
          <h2 class="form__title">登录</h2>
          <input type="text" placeholder="用户名" class="input" v-model="username" />
          <input type="password" placeholder="密码" class="input" v-model="password" />
          <button class="btn" type="submit">登录</button>
          <p v-if="loginError" style="color:red;">{{ loginError }}</p>
        </form>
      </div>
      <!-- 注册表单 -->
      <div class="container__form container--signup">
        <form class="form" @submit.prevent="register">
          <h2 class="form__title">注册</h2>
          <input type="text" placeholder="用户名" class="input" v-model="registerUsername" />
          <input type="password" placeholder="密码" class="input" v-model="registerPassword" />
          <button class="btn" type="submit">注册</button>
          <p v-if="registerError" style="color:red;">{{ registerError }}</p>
          <p v-if="registerSuccess" style="color:green;">{{ registerSuccess }}</p>
        </form>
      </div>
      <!-- 切换面板 -->
      <div class="container__overlay">
        <div class="overlay">
          <div class="overlay__panel overlay--left">
            <button class="btn" @click="isSignUp = false">登录</button>
          </div>
          <div class="overlay__panel overlay--right">
            <button class="btn" @click="isSignUp = true">注册</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import IP from '../../../ipconfig';

export default {
  name: 'LoginPage',
  data() {
    return {
      isSignUp: false,
      username: '',
      password: '',
      registerUsername: '',
      registerPassword: '',
      loginError: '',
      registerError: '',
      registerSuccess: ''
    };
  },
  methods: {
    login() {
      this.loginError = '';
      if (!this.username.trim() || !this.password.trim()) {
        this.loginError = '用户名或密码不能为空';
        return;
      }
      axios.post(`http://${IP}:3000/login`, {
        username: this.username,
        password: this.password
      })
      .then(response => {
        // 登录成功后
        localStorage.setItem("username", response.data.username);
        this.$router.push('/home');
      })
      .catch(error => {
        this.loginError = error.response?.data?.message || '无法连接到后端服务';
      });
    },
    register() {
      this.registerError = '';
      this.registerSuccess = '';
      if (!this.registerUsername.trim() || !this.registerPassword.trim()) {
        this.registerError = '用户名或密码不能为空';
        return;
      }
      axios.post(`http://${IP}:3000/register`, {
        username: this.registerUsername,
        password: this.registerPassword
      })
      .then(() => {
        this.registerSuccess = '注册成功，请登录！';
        this.isSignUp = false;
      })
      .catch(error => {
        this.registerError = error.response?.data?.message || '无法连接到后端服务';
      });
    }
  }
};
</script>

<style>
:root {
  --white: #e9e9e9;
  --gray: #333;
  --blue: #0367a6;
  --lightblue: #008997;
  --button-radius: 0.7rem;
  --max-width: 758px;
  --max-height: 420px;
  font-size: 16px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
    Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
}
</style>

<style scoped>
.container-outer {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  box-sizing: border-box;
  background: transparent;
}

.welcome-title {
  font-size: 2rem;
  color: #2c3e50;
  margin-bottom: 32px;
  letter-spacing: 2px;
  font-weight: bold;
  text-shadow: 0 2px 8px rgba(0,0,0,0.08);
  /* 保证title在表单上方 */
}

.container, .overlay, .overlay__panel {
  background: transparent; /* 不要设置背景色 */
}

.container {
  border-radius: var(--button-radius);
  box-shadow: 0 0.9rem 1.7rem rgba(0, 0, 0, 0.25),
    0 0.7rem 0.7rem rgba(0, 0, 0, 0.22);
  width: 100%;
  max-width: var(--max-width);
  min-height: 400px;
  overflow: hidden;
  position: relative;
  margin: 0;
  background: transparent;
  display: flex;
  flex-direction: column;
  justify-content: center;   /* 让表单内容在容器内也居中 */
  align-items: center;
}

.container__form {
  height: 100%;
  position: absolute;
  top: 0;
  transition: all 0.6s ease-in-out;
}

.container--signin {
  left: 0;
  width: 50%;
  z-index: 2;
}

.container.right-panel-active .container--signin {
  transform: translateX(100%);
}

.container--signup {
  left: 0;
  opacity: 0;
  width: 50%;
  z-index: 1;
}

.container.right-panel-active .container--signup {
  animation: show 0.6s;
  opacity: 1;
  transform: translateX(100%);
  z-index: 5;
}

.container__overlay {
  height: 100%;
  left: 50%;
  overflow: hidden;
  position: absolute;
  top: 0;
  transition: transform 0.6s ease-in-out;
  width: 50%;
  z-index: 100;
}

.container.right-panel-active .container__overlay {
  transform: translateX(-100%);
}

.overlay {
  /* 不要设置 background 或 background-color */
  /* 只保留布局相关样式 */
  height: 100%;
  left: -100%;
  position: relative;
  transform: translateX(0);
  transition: transform 0.6s ease-in-out;
  width: 200%;
}

.container.right-panel-active .overlay {
  transform: translateX(50%);
}

.overlay__panel {
  align-items: center;
  display: flex;
  flex-direction: column;
  height: 100%;
  justify-content: center;
  position: absolute;
  text-align: center;
  top: 0;
  width: 50%;
  background: transparent; /* 完全透明 */
  box-shadow: 0 4px 24px rgba(44, 62, 80, 0.08);
}

.overlay--left {
  transform: translateX(-20%);
}

.container.right-panel-active .overlay--left {
  transform: translateX(0);
}

.overlay--right {
  right: 0;
  transform: translateX(0);
}

.container.right-panel-active .overlay--right {
  transform: translateX(20%);
}

.btn {
  background-color: var(--blue);
  background-image: linear-gradient(90deg, var(--blue) 0%, var(--lightblue) 74%);
  border-radius: 20px;
  border: 1px solid var(--blue);
  color: var(--white);
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: bold;
  letter-spacing: 0.1rem;
  padding: 0.9rem 4rem;
  text-transform: uppercase;
  transition: transform 80ms ease-in;
}

.form > .btn {
  margin-top: 1.5rem;
}

.btn:active {
  transform: scale(0.95);
}

.btn:focus {
  outline: none;
}

.form {
  background-color: var(--white);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  padding: 0 3rem;
  height: 100%;
  text-align: center;
}

.input {
  background-color: #fff;
  border: none;
  padding: 0.9rem 0.9rem;
  margin: 0.5rem 0;
  width: 100%;
}

.form__title {
  font-weight: 300;
  margin: 0;
  margin-bottom: 1.25rem;
}

.error-message {
  color: red;
  margin-top: 1rem;
}

.success-message {
  color: green;
  margin-top: 1rem;
}

@keyframes show {
  0%,
  49.99% {
    opacity: 0;
    z-index: 1;
  }
  50%,
  100% {
    opacity: 1;
    z-index: 5;
  }
}

@media (max-width: 600px) {
  .form {
    padding: 0 0.5rem;
  }
  .welcome-title {
    font-size: 1.2rem;
    margin-bottom: 12px;
  }
}
</style>