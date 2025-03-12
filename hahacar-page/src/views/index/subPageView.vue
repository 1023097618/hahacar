<template>
    <el-container>
        <el-header>
            <el-button type="text" icon="el-icon-arrow-left" @click="goBack">返回</el-button>
        </el-header>
        <el-main :style="{ height: height + 'px' }">
            <router-view></router-view>
        </el-main>
    </el-container>
</template>
<script>
    export default {
        name: 'subPageView',
        data() {
            return {
                height: 0
            }
        },
        methods: {
            goBack() {
                this.$router.go(-1)
            },
            getHeight() {
                this.height = window.innerHeight - 56
            }
        },
        created() {
            this.getHeight()
            window.addEventListener('resize', this.getHeight)
        }
        ,
        destroyed() {
            window.removeEventListener('resize', this.getHeight)
        },
    }
</script>

<style>
    .el-header {
        background-color: #4687ff !important;
        color: #333;
        line-height: 56px !important;
        height: 56px !important;
    }

    .el-header .el-button--text {
        color: #333;
    }
</style>