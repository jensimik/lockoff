<script>
import controllerAPI from "../api/resources/allMethods";
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
    }
  }
}
</script>

<template>
    <h3>Klubmodul</h3>
    <p>Last synced ({{ data.last_sync }}) and {{ data.active_users }} number of active members.</p>
    <button class="warning" @click="forceResyncKlubmodul">resync klubmodul</button>
    <h3>Access log most recent</h3>
    <table class="primary">
        <thead>
            <tr>
                <th>timestamp</th>
                <th>who</th>
            </tr>
        </thead>
        <tbody>
            <tr v-for="log in data.last_access" :key="log.log_id">
                <td>{{ log.timestamp }}</td>
                <td>{{ log.token_type }} / {{ log.user_id }}</td>
            </tr>
        </tbody>
    </table>

</template>

<style scoped>
table {
    width: 100%;
}
</style>