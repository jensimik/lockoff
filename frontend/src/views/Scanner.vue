<script>
import { QrcodeStream } from 'vue-qrcode-reader'

export default {
    name: "scanner",
    data() {
        return {
            code: "",
            error: false,
            paused: false,
        }
    },
    components: {
        QrcodeStream,
    },
    methods: {
        onDetect ([ firstCode ]) {
            this.code = firstCode.rawValue;
            this.paused = true;
        },
        paintOutline(detectedCodes, ctx) {
            for (const detectedCode of detectedCodes) {
                const [firstPoint, ...otherPoints] = detectedCode.cornerPoints

                ctx.strokeStyle = 'red'
                ctx.stroke = '3px'

                ctx.beginPath()
                ctx.moveTo(firstPoint.x, firstPoint.y)
                for (const { x, y } of otherPoints) {
                    ctx.lineTo(x, y)
                }
                ctx.lineTo(firstPoint.x, firstPoint.y)
                ctx.closePath()
                ctx.stroke()
            }
        },
        logErrors(err) {
            this.error = `[${err.name}]: `
            if (err.name === 'NotAllowedError') {
            this.error += 'you need to grant camera access permission'
            } else if (err.name === 'NotFoundError') {
            this.error += 'no camera on this device'
            } else if (err.name === 'NotSupportedError') {
            this.error += 'secure context required (HTTPS, localhost)'
            } else if (err.name === 'NotReadableError') {
            this.error += 'is the camera already in use?'
            } else if (err.name === 'OverconstrainedError') {
            this.error += 'installed cameras are not suitable'
            } else if (err.name === 'StreamApiNotSupportedError') {
            this.error += 'Stream API is not supported in this browser'
            } else if (err.name === 'InsecureContextError') {
            this.error += 'Camera access is only permitted in secure context. Use HTTPS or localhost rather than HTTP.'
            } else {
            this.error += err.message
            }
        }
   }
}
</script>



<template>
    <div class="wrapper">
        <div class="flex two">
            <div>
                <qrcode-stream :paused="paused" :track="paintOutline" @detect="onDetect" @error="logErrors"></qrcode-stream>
            </div>
            <div>
                <p>{{ code }}</p>
                <p v-if="error">{{ error }}</p>
            </div>
        </div>
    </div>
</template>

<style scoped>
.wrapper {
    width: 100%;
    max-width: 300px;
}
</style>