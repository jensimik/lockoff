<script>
import { getMobileOS } from "../misc";
import controllerAPI from "../api/resources/allMethods";
import { APISettings } from "../api/config";
export default {
  name: "Card",
  data() {
    return { 
        user_data: null, 
        os: getMobileOS(),
        baseURL: APISettings.baseURL,
    };
  },
  created() {
    this.fetchUserData();
  },
  methods: {
    fetchUserData() {
        controllerAPI.get_me().then((me_data) => {
            this.user_data = me_data.users;
        }).catch((error) => {
            console.log("failed to fetch me");
            console.log(error);
        })
    }
  }
}
</script>

<template>
    <div class="flex one">
      <div v-for="user in user_data" :key="user.user_id">
        <article class="card">
          <!-- -->
          <header>
            <div class="hleft">
              <h3>{{ user.name }} <span class="membernumber">({{ user.user_id }})</span></h3>
              </div>
            <div class="hright">
              <a target="_blank" :href="baseURL + '/' + user.token + '/qr-code.png'"><img class="qrcode" :src="baseURL + '/' + user.token + '/qr-code.png'"></a>
            </div>
          </header>
          <p>{{ user.member_type }} member exp {{ user.expires }}</p>
          <footer>
            <div class="fleft">
              <a class="button print" target="_blank" :href="baseURL + '/' + user.token + '/membership-card.pdf'">🖨️ pdf print</a>
            </div>
            <div class="fright">
              <a target="_blank" :href="baseURL + '/' + user.token + '/membership-card.pkpass'"><img class="addtoapplewallet" src="/US-UK_Add_to_Apple_Wallet_RGB_101421.svg" /></a>
              <a target="_blank" :href="baseURL + '/' + user.token + '/membership-card'"><img class="addtogooglewallet" src="/svg/enGB_add_to_google_wallet_wallet-button.svg" /></a>
            </div>
          </footer>
        </article>
      </div>
    </div>
</template>

<style scoped>
img[alt="Get it on Google Play"] {
  width: 100%;
}
.print {
  padding-top: 2em;
  padding-bottom: 2em;
  background-color: #000;
  color: #fff;
  font-size: 1.5em;
}
img.addtoapplewallet {
  width: 100%;
  /* margin-left: 50%; */
}
h3 {
  font-size: 1.5em;
}
h4 {
  margin: 0;
  padding: 0;
}
.membernumber {
  font-size: 0.5em;
}
.qrcode {
  height: 1.5em;
}
.button {
  width: 100%;
}
.hright {
  display: inline-block;
  text-align: right;
  width: 2em;
}
.hleft {
  display: inline-block;
  width: calc(100% - 2em);
}
.fright {
  display: inline-block;
  text-align: right;
  padding-left: 0.5em;
  width: 50%;
}
.fleft {
  display: inline-block;
  width: 50%;
  padding-right: 0.5em;
}
</style>

