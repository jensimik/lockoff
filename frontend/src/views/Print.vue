<script>
import controllerAPI from "../api/resources/allMethods";

export default {
  name: "Print Daytickets",
  props: ['foo'],
  setup(props) {
    console.log(props.pages_to_print);
    this.pages_to_print = props.pages_to_print;
  },
  data() {
    return { 
        pages_to_print: 1,
        data: {}, 
    };
  },
  created() {
    this.fetchData();
  },
  methods: {
    fetchData() {
        controllerAPI.generate_daytickets(this.pages_to_print).then((print_data) => {
            this.data = print_data;
        }).catch((error) => {
            console.log("failed to fetch print data");
            console.log(error);
        })
    },
  }
}
</script>

<template>
    <div class="print-container">
        <article class="ticket" v-for="ticket in data" :key="ticket.dayticket_id">
            <img class="qrcode" :src="'https://lockoff-api.gnerd.dk/admin/' + ticket.dl_token + '/qr-code.png'" />
            <div class="padding"></div>
            <div class="ticket-text">
                <p class="nkk-title">Nørrebro klatreklub</p>
                <p>#{{ ticket.dayticket_id }}</p>
            </div>
        </article>
    </div>
</template>

<style scoped>
.print-container {
    width: 100%;
}
.ticket {
    width: 33%;
    display: inline-block;
    margin: 0 0 2mm 0;
    padding: 0;
    height: 25mm;
}
.qrcode {
    width: 25mm;
    height: 25mm;
    display: inline-block;
}
.padding {
    width: 2.5mm;
    display: inline-block;
}
.ticket-text {
    display: inline-block;
    height: 25mm;
    width: 35mm;
    vertical-align: top;
    padding: 1mm 1mm 1mm 0;
    border-top: 1mm dashed #000;
    border-bottom: 1mm dashed #000;
    border-right: 1mm dashed #000;
}
.ticket-text > p {
    text-align: center;
    padding: 0;
    margin: 0;
}

@media print { 
    @page { margin: 5mm }
    .ticket {
        page-break-inside: avoid;
    } 
    body {
        max-width: none;
        font: 10pt Arial, Helvetica, sans-serif;
        line-height: 1;
        background: #fff !important;
        color: #000;
    }
 }
</style>