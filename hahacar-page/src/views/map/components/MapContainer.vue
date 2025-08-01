<template>
    <el-row :gutter="20" :style="{ width: '100%', height: mapHeight + 'px' }">
        <!-- 左侧地图区域 -->
        <el-col :span="16" style="height: 100%;">
            <div ref="mapContainer" style="width: 100%; height: 100%;"></div>
        </el-col>
        <!-- 右侧预警信息滚动区域 -->
        <el-col :span="8" style="height: 100%;">
            <div class="alert-container">
                <div
                    v-for="(alert, index) in alertMessages"
                    :key="index"
                    class="alert-message"
                    @click="goToAlert(alert.alertId)"
                >

                    <i class="fas fa-exclamation-triangle"></i>
                    <div class="alert-info">
                        <p class="alert-camera">{{ alert.cameraName }}</p>
                        <p class="alert-rule">{{ alert.ruleRemark }}</p>
                    </div>
                </div>
            </div>
        </el-col>
    </el-row>
</template>

<script>
    import { loadAMap } from '@/utils/loadAMap.js'


    export default {
        name: 'MapAlertContainer',
        data() {
            return {
                mapInstance: null,
                mapHeight: 400,
                markers: {},
                defaultIconUrl: require('@/assets/default_marker.png'),
                alertIconUrl: require('@/assets/red_marker.png'),
                cameras: []
            }
        },
        computed: {
            // 通过 Vuex getter 获取预警信息和摄像头状态
            alertMessages() {
                return this.$store.getters.alertMessages
            },
            cameraSituations() {
                return this.$store.getters.cameraSituations
            },
            currentTheme() {
                return this.$store.getters.user.style;
            },
        },
        beforeDestroy() {
            window.removeEventListener('resize', this.getHeight)
        },
        watch: {
            // 当摄像头状态变化时更新 marker 图标
            cameraSituations: {
                handler() {
                    this.updateMarkersStatus()
                },
                deep: true
            },
            currentTheme(newVal) {
                if (this.mapInstance) {
                    this.mapInstance.setMapStyle(this.getMapStyleByTheme(newVal));
                }
            }
        },
        methods: {
            getHeight() {
                this.mapHeight = window.innerHeight - 56 - 70
            },
            initMap() {
                let center = [116.397428, 39.90923]
                this.mapInstance = new window.AMap.Map(this.$refs.mapContainer, {
                    center: center,
                    zoom: 14,
                    mapStyle: this.getMapStyleByTheme(this.currentTheme),
                    viewMode: '3D',
                    pitch: 0
                })

                const controlBar = new window.AMap.ControlBar({
                    position: { right: '10px', top: '10px' }
                })

                const trafficLayer = new window.AMap.TileLayer.Traffic({
                    zIndex: 10,
                    zooms: [7, 22]
                })

                trafficLayer.setMap(this.mapInstance)
                controlBar.addTo(this.mapInstance)
            },
            addMarkers() {
                if (this.cameras && this.cameras.cameras && this.cameras.cameras.length > 0) {
                    let totalLng = 0, totalLat = 0
                    this.cameras.cameras.forEach((camera) => {
                        totalLng += parseFloat(camera.cameraLocation[0])
                        totalLat += parseFloat(camera.cameraLocation[1])
                    })
                    const center = [
                        totalLng / this.cameras.cameras.length,
                        totalLat / this.cameras.cameras.length
                    ]
                    this.mapInstance.setCenter(center)
                }
                if (this.cameras && this.cameras.cameras) {
                    this.cameras.cameras.forEach((camera) => {
                        const position = [
                            parseFloat(camera.cameraLocation[0]),
                            parseFloat(camera.cameraLocation[1])
                        ]
                        const marker = new window.AMap.Marker({
                            position,
                            title: camera.cameraName,
                            icon: this.defaultIconUrl,
                            offset: new window.AMap.Pixel(-26, -60),
                            // zooms: [12, 20]
                        })
                        marker.cameraId = camera.cameraId
                        this.markers[camera.cameraId] = marker
                        this.mapInstance.add(marker)
                    })
                }
                this.updateMarkersStatus()
            },
            getMapStyleByTheme(themeValue) {
                switch (themeValue) {
                    case 1: // 浅色
                        return 'amap://styles/normal';
                    case 2: // 深色
                        return 'amap://styles/blue';
                    case 3: // 跟随系统
                        return window.matchMedia('(prefers-color-scheme: dark)').matches
                            ? 'amap://styles/blue'
                            : 'amap://styles/normal';
                    default:
                        return 'amap://styles/normal';
                }
            },
            init(cameras) {
                this.cameras = cameras
                this.getHeight()
                window.addEventListener('resize', this.getHeight)
                loadAMap()
                    .then(() => {
                        this.initMap()
                        this.addMarkers()
                    })
                    .catch((error) => {
                        console.error('地图加载出错:', error)
                    })
            },
            goToAlert(alertId) {
                this.$router.push({ path: '/alertList', query: { alertId } });
            },
            updateMarkersStatus() {
                Object.keys(this.cameraSituations).forEach(cameraId => {
                    if (this.markers[cameraId]) {
                        if (this.cameraSituations[cameraId].alert) {
                            this.markers[cameraId].setIcon(this.alertIconUrl)
                        } else {
                            this.markers[cameraId].setIcon(this.defaultIconUrl)
                        }
                    }
                })
            }
        }
    }
</script>


<style scoped>
    .alert-container {
        height: 100%;
        overflow-y: auto;
        padding: 10px;
        border-left: 1px solid #ebeef5;
        background-color: #f9f9f9;
    }
    .alert-message {
        margin-bottom: 10px;
        padding: 10px;
        background-color: #fff;
        border-radius: 4px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        display: flex;
        align-items: center;
        cursor: pointer;
        transition: background-color 0.3s;
    }
    .alert-message:hover {
        background-color: #f0f0f0;
    }
    .alert-message i {
        font-size: 20px;
        color: #e74c3c;
        margin-right: 10px;
    }
    .alert-info p {
        margin: 0;
        line-height: 1.4;
    }
    .alert-camera {
        font-weight: bold;
    }
    .alert-rule {
        color: #555;
    }
</style>