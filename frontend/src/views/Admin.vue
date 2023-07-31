<script>
import controllerAPI from "../api/resources/allMethods";
export default {
  name: "Admin dashboard",
  data() {
    return { 
        data: null, 
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
    }
  }
}
</script>

<template>
    <h3>Access log most recent</h3>
    <table class="primary">
        <thead>
            <tr>
                <td>timestamp</td>
                <td>who</td>
            </tr>
        </thead>
        <tbody>
            <tr v-for="l in data.access_log">
                <td>{{ l.timestamp }}</td>
                <td>{{ l.token_type }} / {{ l.user_id }}</td>
            </tr>
        </tbody>
    </table>

</template>