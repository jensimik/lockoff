<script>
import { QrcodeStream } from 'vue-qrcode-reader'
import controllerAPI from "../api/resources/allMethods";

export default {
    name: "scanner",
    data() {
        return {
            show: "",
            paused: false,
            error: "",
            constraints: {
                facingMode: {exact: 'environment'},
                width: {
                    exact: 300
                },
                height: {
                    exact: 300
                }
            }
        }
    },
    components: {
        QrcodeStream,
    },
    methods: {
        onDetect ([ firstCode ]) {
            this.code = firstCode.rawValue;
            controllerAPI.check_token(this.code).then((data) => {
                this.show = data;
            }).catch((error) => {
                this.show = {c: error.name, m: error.message};
            });
            // this.paused = true;
        },
        paintOutline(detectedCodes, ctx) {
            for (const detectedCode of detectedCodes) {
                const [firstPoint, ...otherPoints] = detectedCode.cornerPoints

                ctx.strokeStyle = 'red'

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
    <div class="flex one jcc">
        <div class="cam">
            <qrcode-stream :constraints="constraints" :paused="paused" :track="paintOutline" @detect="onDetect" @error="logErrors"></qrcode-stream>
        </div>
        <div>
            <pre>{{ show }}{{ error }}</pre>
        </div>
    </div>
</template>

<style scoped>

/deep/ .qrcode-stream-camera {
    width: 300px;
    height: 300px;
}
/deep/ .qrcode-stream-overlay {
    width: 300px;
    height: 300px;
}
.cam {
    width: 300px;
    height: 300px;
    max-width: 300px;
    max-height: 300px;
    position:relative;
}
.jcc {
    justify-content: center;
}
</style>