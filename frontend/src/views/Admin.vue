<script>
import controllerAPI from "../api/resources/allMethods";
import router from "../router";

export default {
  name: "Admin dashboard",
  data() {
    return { 
        data: {}, 
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
        router.push({name: "dayticket_print"});
        return false;
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
    </div>
    <div class="flex two">
        <h3>Daytickets</h3>
        <div class="right">
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
                    <th>used</th>
                    <th>unused</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="batch in data.dt_stats" :key="batch.batch_id">
                    <td>{{ batch.batch_id }}</td>
                    <td>{{ batch.used }}</td>
                    <td>{{ batch.unused }}</td>
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
                    <th>who</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="log in data.member_access" :key="log.log_id">
                    <td>{{ log.timestamp }}</td>
                    <td>{{ log.token_type }} / {{ log.user_id }}</td>
                </tr>
            </tbody>
        </table>
    </div>
</template>

<style scoped>
.bold {
    font-weight: bolder;
}
.right {
    text-align: right;
}
</style>