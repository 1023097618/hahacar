
<template>
  <UploadPicture :urls.sync="vedioUrls" ref="uploadPicture" />
</template>
  
<script>
  import UploadPicture from '@/components/UploadPicture.vue'
  export default {
    name: 'vedioView',
    data() {
      return {
        vedioUrls:[]
      };
    },
    components: {
      UploadPicture
    }
  }
</script>