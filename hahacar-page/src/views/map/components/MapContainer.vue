<template>
    <div ref="mapContainer" :style="{width: '100%', height: mapHeight+ 'px' }"></div>
</template>

<script>
    import { loadAMap } from '@/utils/loadAMap.js';

    export default {
        name: 'MapContainer',
        data() {
            return {
                mapInstance: null,
                mapHeight: 400
            };
        },
        mounted() {
            // 1. 动态加载高德地图脚本
            loadAMap()
                .then(() => {
                    // 2. 脚本加载成功后，再初始化地图
                    this.initMap();
                })
                .catch((error) => {
                    console.error('地图加载出错:', error);
                });
        },
        methods: {
            initMap() {
                // this.$refs.mapContainer 即 template 中的 div
                this.mapInstance = new window.AMap.Map(this.$refs.mapContainer, {
                    center: [116.397428, 39.90923], // 默认中心点（可换成你的坐标）
                    zoom: 11,
                    mapStyle: 'amap://styles/blue'
                });

                // 如果需要在地图上添加点标记、范围圈等，可以继续操作
                const marker = new window.AMap.Marker({
                    position: [116.397428, 39.90923]
                });
                this.mapInstance.add(marker);
            },
            getHeight() {
                //56见index/indexView   70见
                this.mapHeight = window.innerHeight - 56 - 70
            },
        },
        created() {
            this.getHeight()
            window.addEventListener('resize', this.getHeight)
        }
        ,
        destroyed() {
            window.removeEventListener('resize', this.getHeight)
        }
    };
</script>

<style scoped>
    /* 在这里写组件内的样式 */
</style>