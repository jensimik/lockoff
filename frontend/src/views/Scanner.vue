<script>
import { QrcodeStream, QrcodeDropZone, QrcodeCapture } from 'vue-qrcode-reader'

export default {
    name: "scanner",
    data() {
        return {
            code: "",
        }
    },
    components: {
        QrcodeStream,
    },
    methods: {
        onDetect (detectedCode) {
            console.log(detectedCode);
            this.code = detectedCode;
        }
    }
}
</script>



<template>
    <qrcode-stream @detect="onDetect"></qrcode-stream>
    <p>{{ code }}</p>
</template>