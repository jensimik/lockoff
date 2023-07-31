<script>
import { QrcodeStream, QrcodeDropZone, QrcodeCapture } from 'vue-qrcode-reader'

export default {
    name: "scanner",
    components: {
        QrcodeStream,
    },
    methods: {
        onDetect (detectedCode) {
            console.log(detectedCode);
        }
    }
}
</script>



<template>
    <qrcode-stream @detect="onDetect"></qrcode-stream>
</template>