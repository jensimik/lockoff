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
              <a class="button" target="_blank" :href="baseURL + '/' + user.token + '/membership-card.pdf'">🖨️ pdf for print</a>
            </div>
            <div class="fright">
              <a class="button" target="_blank" :href="baseURL + '/' + user.token + '/membership-card.pkpass'">📱 mobile pass<span v-if="os== 'Android'">*</span></a>
            </div>
            <a v-if="os == 'iOS'" target="_blank" :href="baseURL + '/' + user.token + '/membership-card.pkpass'"><img class="addtoapplewallet" src="/US-UK_Add_to_Apple_Wallet_RGB_101421.svg" /></a>
          </footer>
        </article>
        </div>
        <div v-if="os == 'Android'">
          <p>* to use the digital wallet on android phones you need an app - i recommend one of these apps:</p>
          <div class="flex two">
            <div>
              <h4>WalletPass</h4>
              <a target="_blank" href='https://play.google.com/store/apps/details?id=io.walletpasses.android'><img alt='Get it on Google Play' src='https://play.google.com/intl/en_us/badges/static/images/badges/en_badge_web_generic.png'/></a>
            </div>
            <div>
              <h4>PassWallet</h4>
              <a target="_blank" href='https://play.google.com/store/apps/details?id=com.attidomobile.passwallet'><img alt='Get it on Google Play' src='https://play.google.com/intl/en_us/badges/static/images/badges/en_badge_web_generic.png'/></a>
            </div>
          </div>
          <p>be sure to <a target="_blank" href="https://support.passcreator.com/space/KB/22347871/Location+based+notifications+-+troubleshooting#Location-based-notifications-on-Android">enable geo and ibeacon in the app</a></p>
        </div>
    </div>
</template>

<style scoped>
img[alt="Get it on Google Play"] {
  width: 100%;
}
img.addtoapplewallet {
  width: 50%;
  margin-left: 50%;
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

