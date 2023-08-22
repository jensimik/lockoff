<script>
import controllerAPI from "../api/resources/allMethods";
import router from "../router";

export default {
  name: "Admin dashboard",
  data() {
    return { 
        data: {}, 
        pages_to_print: 1,
        fixed_card_name: "",
    };
  },
  created() {
    this.fetchData();
  },
  methods: {
    fetchData() {
        controllerAPI.system_status().then((status_data) => {
            this.data = status_data;
        }).catch((error) => {
            console.log("failed to fetch status data");
            console.log(error);
        })
    },
    forceResyncKlubmodul(e) {
        e.target.disabled = true;
        controllerAPI.klubmodul_force_resync().then(() => {
            console.log("force resync");
        })
    },
    print() {
        router.push({name: "dayticket_print", query: {pages_to_print: this.pages_to_print}});
        return false;
    },
    generate_fixed_card() {
        controllerAPI.create_fixed_card(this.fixed_card_name).then(() => {
            console.log("card created: " + this.fixed_card_name);
            window.location.reload();
        });
    },
    remove_fixed_card(card_id) {
        controllerAPI.remove_fixed_card(card_id).then(() => {
            console.log("removed");
            window.location.reload();
        })
    }
  }
}
</script>

<template>
    <div class="flex two">
        <h3>Klubmodul</h3>
        <div class="right">
            <button class="warning" @click="forceResyncKlubmodul">resync klubmodul</button>
        </div>
    </div>
    <div class="flex one">
        <p><span class="bold">{{ data.active_users }}</span> active members and last synced <span class="bold">{{ data.last_sync }}</span></p>
        <p><span class="bold">{{ data.total_issued }}</span> members have issued access cards (hereof {{ data.digital_issued }} digital and {{ data.print_issued }} print)</p>
    </div>
    <div class="flex two">
        <h3>Fixed cards</h3>
        <div class="right">
            <input id="fixed_card_name" type="text" name="fixed_card_name" v-model="fixed_card_name" placeholder="name of card" /><button @click="generate_fixed_card">generate fixed card</button>
        </div>
    </div>
    <div class="flex one">
        <table>
            <thead>
                <tr>
                    <th>name</th>
                    <th>qr_code</th>
                    <th></th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="ft in data.fixed_tickets" :key="ft.id">
                    <td>{{ ft.name }}</td>
                    <td class="center"><a target="_blank" :href="'https://lockoff-api.gnerd.dk/admin/othertickets/' + ft.dl_token + '/qr-code.png'"><img class="qr_code" :src="'https://lockoff-api.gnerd.dk/admin/othertickets/' + ft.dl_token + '/qr-code.png'" /></a></td>
                    <td class="right"><button @click="remove_fixed_card(ft.id)">remove</button></td>
                </tr>
            </tbody>
        </table>
    </div>
    <div class="flex two">
        <h3>Daytickets</h3>
        <div class="right">
            <input id="pages_to_print" type="number" v-model="pages_to_print" />
            <button @click="print">generate print</button>
        </div>
    </div>
    <div class="flex one">
        <p><span class="bold">{{ data.dayticket_reception }}</span> tickets in the reception and <span class="bold">{{ data.dayticket_used }}</span> used in total this season.</p>
    </div>
    <div class="flex one">
        <table>
            <thead>
                <tr>
                    <th>batch_id</th>
                    <th class="center">ticket_ids</th>
                    <th class="right">used</th>
                    <th class="right">unused</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="batch in data.dt_stats" :key="batch.batch_id">
                    <td>{{ batch.batch_id.substring(0,16) }}</td>
                    <td class="center">{{ batch.range_start }}-{{ batch.range_end }}</td>
                    <td class="right">{{ batch.used }}</td>
                    <td class="right">{{ batch.unused }}</td>
                </tr>
            </tbody>
        </table>

    </div>
    <div class="flex one">
        <h3>Access log most recent</h3>
        <table class="primary">
            <thead>
                <tr>
                    <th>timestamp</th>
                    <th>id</th>
                    <th>type</th>
                    <th>media</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="log in data.member_access" :key="log.id">
                    <td>{{ log.timestamp.substring(0,16) }}</td>
                    <td>{{ log.obj_id }}</td>
                    <td>{{ log.token_type }}</td>
                    <td>{{ log.token_media }}</td>
                </tr>
            </tbody>
        </table>
    </div>
</template>

<style scoped>
img.qr_code {
    width: 1.5em;
    height: 1.5em;
}
td {
    padding-right: 0.6em;
}
th {
    padding-right: 0.6em;
}
.bold {
    font-weight: bolder;
}
.right {
    text-align: right;
}
.center {
    text-align: center;
}
#pages_to_print {
    display: inline-block;
    width: 5em;
}
#fixed_card_name {
    display: inline-block;
    width: 6em;
}
</style>