<script>
import { QrcodeStream } from 'vue-qrcode-reader'

export default {
    name: "scanner",
    data() {
        return {
            code: "",
            error: false,
        }
    },
    components: {
        QrcodeStream,
    },
    methods: {
        onDetect (detectedCodes) {
            console.log(detectedCodes);
            this.code = detectedCodes[0].rawValue;
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
            this.error = true;
        }
    }
}
</script>



<template>
    <div class="flex two">
        <div>
            <qrcode-stream :track="paintOutline" @detect="onDetect" @error="logErrors"></qrcode-stream>
        </div>
        <div>
            <p>{{ code }}</p>
            <p v-if="error">could not load camera somehow? are you on mobile?</p>
        </div>
    </div>
</template>