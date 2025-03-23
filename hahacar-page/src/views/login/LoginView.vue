<template>
	<div class="container" :style="{ height:containerConfig.height+'px' }">
		<div class="screen">
			<div class="screen__content">
				<div class="logo-container">
					<!-- 这里替换为实际 logo 路径或组件 -->
					<img src="@/assets/logo.png" alt="Logo" class="logo" />
				</div>
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
						<input type="password" class="login__input" placeholder="密码" v-model="password">
					</div>
					<button class="button login__submit" @click="SendLogin">
						<span class="button__text">登录</span>
						<i class="button__icon fas fa-chevron-right"></i>
					</button>
				</form>
				<div class="password-reset">
					<h3 @click="findPassword" class="password-reset-text">找回密码</h3>
				</div>
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
				password: "",
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
			SendLogin(event) {
				event.preventDefault();
				this.$store.dispatch('LoginByUserName', { username: this.username, password: this.password }).then(() => {
					this.$router.push('/').catch(err => {
						console.log(err)
					})
					console.log('success')
				}).catch(err => {
					if(err.code==="400"){
						this.errorMsg=err.msg
					}
				})
			},
			findPassword(event) {
				event.preventDefault();
				this.$router.push("/resetPasswordByOldPassword");
			}
		},
		created() {
			this.getHeight()
			window.addEventListener('resize', this.getHeight)
		},
	}
</script>
<style scoped>
	/* 容器背景：改用你提供的图片，示例路径可根据实际项目放置位置调整 */
	.container {
		display: flex;
		align-items: center;
		justify-content: center;
		background: url('@/assets/bg.png') no-repeat center center;
		background-size: cover;
		/* 这里保持原有的最小高度逻辑，如果希望完全铺满，可以去掉 height 或者做其他适配 */
	}

	/* 外层屏幕容器：用半透明背景与外部区分，或使用渐变 */
	.screen {
		background: rgba(0, 0, 0, 0.5);
		/* 半透明深色背景 */
		position: relative;
		height: 600px;
		width: 360px;
		box-shadow: 0px 0px 24px #333;
		/* 适当变暗 */
	}

	/* 内部内容保持相对定位即可 */
	.screen__content {
		z-index: 1;
		position: relative;
		height: 100%;
		/* 可以增加一些内边距，避免与顶部太贴近 */
	}

	.logo-container {
		text-align: center;
		margin-top: 20px; /* 与顶部保持距离 */
	}

	.logo {
		height: 150px;
		/* 如果需要自适应宽度，可以去掉固定高度，加上 max-width: 100% 等 */
	}

	/* 背景形状，可根据需要调节颜色和透明度 */
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
		opacity: 0.3;
		/* 形状透明度，可根据需要调整 */
	}

	.screen__background__shape1 {
		height: 520px;
		width: 520px;
		background: #00FFFF;
		/* 浅蓝色示例，可自行调整 */
		top: -50px;
		right: 120px;
		border-radius: 0 72px 0 0;
	}

	.screen__background__shape2 {
		height: 220px;
		width: 220px;
		background: #0066FF;
		/* 蓝色示例，可自行调整 */
		top: -172px;
		right: 0;
		border-radius: 32px;
	}

	.screen__background__shape3 {
		height: 540px;
		width: 190px;
		background: linear-gradient(270deg, #2F80ED, #56CCF2);
		/* 渐变示例 */
		top: -24px;
		right: 0;
		border-radius: 32px;
	}

	/* 登录表单 */
	.login {
		width: 320px;
		padding: 30px;
		padding-top: 0px;
		/* 保持与顶部装饰的间距 */
	}

	/* 登录字段 */
	.login__field {
		padding: 20px 0px;
		position: relative;
	}

	.login__icon {
		position: absolute;
		top: 30px;
		color: #bbb;
		/* 图标颜色 */
	}

	/* 输入框 */
	.login__input {
		border: none;
		border-bottom: 2px solid #D1D1D4;
		background: none;
		padding: 10px;
		padding-left: 24px;
		font-weight: 700;
		width: 75%;
		transition: .2s;
		color: #fff;
		/* 深色背景下，文字改成白色 */
	}

	.login__input:focus,
	.login__input:hover {
		outline: none;
		border-bottom-color: #00FFFF;
		/* 聚焦时改为亮色 */
	}

	/* 登录按钮 */
	.login__submit {
		background: #1B1B1B;
		font-size: 14px;
		margin-top: 30px;
		padding: 16px 20px;
		border-radius: 26px;
		border: 1px solid #4C4C4C;
		text-transform: uppercase;
		font-weight: 700;
		display: flex;
		align-items: center;
		width: 100%;
		color: #fff;
		box-shadow: 0px 2px 2px #000;
		cursor: pointer;
		transition: .2s;
	}

	.login__submit:hover {
		background: #333;
		border-color: #00FFFF;
	}

	/* 按钮图标 */
	.button__icon {
		font-size: 24px;
		margin-left: auto;
		color: #00FFFF;
		/* 与边框焦点色呼应 */
	}

	/* 找回密码链接 */
	.password-reset {
		position: absolute;
		height: 140px;
		width: 160px;
		text-align: center;
		bottom: 0px;
		right: 0px;
		color: #fff;
	}

	.password-reset-text {
		cursor: pointer;
		text-decoration: underline;
		font-size: 14px;
	}

	.error-msg {
		background-color: rgba(255, 0, 0, 0.2); /* 半透明红色背景 */
		color: #ff8080; /* 文本颜色可与背景对应 */
		padding: 10px;
		margin-bottom: 10px;
		border-radius: 4px;
		text-align: center;
		font-weight: bold;
	}
</style>