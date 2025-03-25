<template>
	<div class="container" :style="{ height:containerConfig.height+'px' }">
		<div class="screen">
			<div class="close-button" @click="goToLogin">
				<i class="fas fa-times"></i>
			</div>
			<div class="screen__content">
				<form class="login">
					<div v-if="errorMsg" class="error-msg">
						{{ errorMsg }}
					</div>
					<div class="login__field">
						<i class="login__icon fas fa-user"></i>
						<input type="text" class="login__input" placeholder="用户名" v-model="username">
					</div>
                    <div class="login__field">
						<i class="login__icon fas fa-lock"></i>
						<input type="password" class="login__input" placeholder="老密码" v-model="oldPassword">
					</div>
					<div class="login__field">
						<i class="login__icon fas fa-lock"></i>
						<input type="password" class="login__input" placeholder="新密码" v-model="newPassword">
					</div>
                    <div class="login__field">
						<i class="login__icon fas fa-lock"></i>
						<input type="password" class="login__input" placeholder="确认密码" v-model="confirmNewPassword">
					</div>
					<button class="button login__submit" @click="SendReset">
						<span class="button__text">找回密码</span>
						<i class="button__icon fas fa-chevron-right"></i>
					</button>
				</form>
			</div>
			<div class="screen__background">
				<span class="screen__background__shape screen__background__shape3"></span>
				<span class="screen__background__shape screen__background__shape2"></span>
				<span class="screen__background__shape screen__background__shape1"></span>
			</div>
		</div>
	</div>
</template>

<script>

	export default {
		name: "LoginView",
		data() {
			return {
				containerConfig: {
					height: 600
				},
				username: "",
                oldPassword:"",
				newPassword: "",
                confirmNewPassword:"",
				errorMsg: ""
			}
		},
		methods: {
			getHeight() {
				// 和screen的高度保持一致
				if (window.innerHeight >= 600) {
					this.containerConfig.height = window.innerHeight
				} else {
					this.containerConfig.height = 600
				}

			},
			SendReset(event) {
				event.preventDefault();
				if(this.newPassword!==this.confirmNewPassword){
					this.$message.error('密码不一致');
					return;
				}
				this.$store.dispatch('ChangePasswordByOldpassword', {username:this.username,oldPassword:this.oldPassword,newPassword:this.newPassword}).then(() => {
					this.$router.push('/login').catch(err => {
						console.log(err)
					})
					console.log('success')
				}).catch(err => {
					console.log(err)
				})
			},
			goToLogin(){
				this.$router.push("/login")
			}
		},
		created() {
			this.getHeight()
			window.addEventListener('resize', this.getHeight)
		}
	}
</script>
<style scoped>
.container {
  display: flex;
  align-items: center;
  justify-content: flex-start;
	padding-left: 23%;
  background: url('@/assets/bg.png') no-repeat center center;
  background-size: cover;
}

/* 
   .screen 使用半透明深色背景，与外部背景图区分
*/
.screen {
  position: relative;
  height: 600px;
  width: 360px;
  background: rgba(0, 0, 0, 0.5); /* 半透明深色背景 */
  box-shadow: 0px 0px 24px #333;  /* 适当的阴影 */
}

/* 内部内容保持相对定位 */
.screen__content {
  z-index: 1;
  position: relative;
  height: 100%;
  /* 可根据需要增加内边距 */
}

/* 背景形状，使用较淡或半透明色，避免干扰表单 */
.screen__background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
  clip-path: inset(0 0 0 0);
}

.screen__background__shape {
  transform: rotate(45deg);
  position: absolute;
  opacity: 0.3; /* 可根据需要调整形状可见度 */
}

/* 以下示例颜色仅供参考，可根据整体风格更换 */
.screen__background__shape1 {
  height: 520px;
  width: 520px;
  background: #FFF; 
  top: -50px;
  right: 120px;
  border-radius: 0 72px 0 0;
}

.screen__background__shape2 {
  height: 220px;
  width: 220px;
  background: #6C63AC;
  top: -172px;
  right: 0;
  border-radius: 32px;
}

.screen__background__shape3 {
  height: 540px;
  width: 190px;
  background: linear-gradient(270deg, #5D54A4, #6A679E);
  top: -24px;
  right: 0;
  border-radius: 32px;
}

/* 表单区 */
.login {
  width: 320px;
  padding: 30px;
  padding-top: 37px; /* 原本就设置为37，可保持 */
}

/* 输入框字段 */
.login__field {
  padding: 20px 0;
  position: relative;
}

/* 输入框图标 */
.login__icon {
  position: absolute;
  top: 30px;
  color: #bbb; /* 改成浅色更易读 */
}

/* 输入框 */
.login__input {
  border: none;
  border-bottom: 2px solid #D1D1D4;
  background: none;
  padding: 10px 24px 10px 24px;
  font-weight: 700;
  width: 75%;
  transition: .2s;
  color: #fff; /* 在深色背景上使用白色文字 */
}

.login__input:focus,
.login__input:hover {
  outline: none;
  border-bottom-color: #00FFFF; /* 聚焦时突出颜色，可根据需求修改 */
}

/* 提交按钮 */
.login__submit {
  background: #fff;
  font-size: 14px;
  margin-top: 30px;
  padding: 16px 20px;
  border-radius: 26px;
  border: 1px solid #D4D3E8;
  text-transform: uppercase;
  font-weight: 700;
  display: flex;
  align-items: center;
  width: 100%;
  color: #4C489D;
  box-shadow: 0px 2px 2px #5C5696;
  cursor: pointer;
  transition: .2s;
}

.login__submit:hover {
  border-color: #6A679E;
}

/* 按钮文字、图标 */
.button__text {
  text-align: center;
}

.button__icon {
  font-size: 24px;
  margin-left: auto;
  color: #7875B5;
}

/* 关闭按钮样式，可视需要微调 */
.close-button {
  cursor: pointer;
  position: absolute;
  top: 15px;
  right: 15px;
  width: 30px;
  height: 30px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.2);
  transition: background 0.3s ease;
  z-index: 2;
}

.close-button i {
  color: #4C489D;
  font-size: 18px;
}

.close-button:hover {
  background: rgba(255, 255, 255, 1);
}
</style>