
<template>
  <UploadMedia :urls.sync="vedioUrls" ref="UploadMedia" />
</template>
  
<script>
  import UploadMedia from '@/components/UploadMedia.vue'
  export default {
    name: 'uploadView',
    data() {
      return {
        vedioUrls:[]
      };
    },
    components: {
      UploadMedia
    }
  }
</script>