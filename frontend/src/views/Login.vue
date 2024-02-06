<script setup>
import { ref } from 'vue';
import { useRoute } from 'vue-router';
import { toast } from 'vue3-toastify';
import controllerAPI from '../api/resources/allMethods';
import { getMobileOS } from '../misc';
import router from '../router';
import { setWithExpiry } from '../store';

var step = ref("username");
var username = ref("");
var username_type = ref("mobile");
var totp = ref("");
var os = ref(getMobileOS());
const route = useRoute();
const next_hop = route.query.next;

const ac = new AbortController();

const options = ref([
  { text: 'verify mobile', value: 'mobile' },
  { text: 'verify email', value: 'email' },
])

const selector_change = async(e) => {
  username.value = "";
}


const occupancy = ref({
  currently: 0,
  historical: 0
})

controllerAPI.system_occupancy().then((ocdata) => {
  occupancy.value.currently = ocdata.currently;
  occupancy.value.historical = ocdata.historical;
});

const mobile_update = async(e) => {
  e.target.style.setProperty('--_otp-digit', e.target.selectionStart);
  if (username.value.length == 8) {
    e.target.blur();
    step.value = "totp";
    window.scrollTo({ top: 0});
    controllerAPI.request_totp(username.value, username_type.value).then(() => {
      toast.info("check your " + username_type.value + " for the code");
      // listen for OTP token on sms automatic
      if ('OTPCredential' in window) {
          const input = document.querySelector('input[autocomplete="one-time-code"]');
          if (!input) return;
          // Invoke the WebOTP API
          navigator.credentials.get({
            otp: { transport:['sms'] },
            signal: ac.signal
          }).then(otp => {
            input.value = otp.code;
          }).catch(err => {
            console.log(err);
          });
      }
    }).catch((e) => {
      step.value = "username";
      username.value = "";
      toast.error("unknown " + username_type.value + " or no connection to backend");
    })
  }
}

const email_update = async(e) => {
  e.target.blur();
  step.value = "totp";
  window.scrollTo({ top: 0});
  controllerAPI.request_totp(username.value, username_type.value).then(() => {
    toast.info("check your " + username_type.value + " for the code");
  }).catch((e) => {
      step.value = "username";
      username.value = "";
      toast.error("unknown " + username_type.value + " or no connection to backend");
  })
}



const totp_update = async(e) => {
  e.target.style.setProperty('--_otp-digit', e.target.selectionStart);
  if (totp.value.length == 6) {
    e.target.blur();
    // Cancel the WebOTP API.
    ac.abort();
    controllerAPI.login(username.value, username_type.value, totp.value).then((token_data) => {  
        toast.success("logged in");
        setWithExpiry("access_token", token_data.access_token, 7100 * 1000);
        if (next_hop)
            setTimeout(() => router.push({name: next_hop}), 500);
        else
            setTimeout(() => router.push({name: "card"}), 500);
    }).catch((e) => {
        toast.error("failed to login - check if your " + username_type.value + " and code is correct and try again later");
        username.value = "";
        totp.value = "";
        step.value = "username";
    })
  }
}

const tryagain = async(e) => {
  username.value = "";
  totp.value = "";
  step.value = "username";
  return false
}

</script>

<template>
  <div v-show="step == 'username'">
    <div class="flex one">
      <svg id="logo" xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 512 511" style="shape-rendering:geometricPrecision; text-rendering:geometricPrecision; image-rendering:optimizeQuality; fill-rule:evenodd; clip-rule:evenodd" xmlns:xlink="http://www.w3.org/1999/xlink">
        <g><path style="opacity:1" fill="#fefefe" d="M 231.5,1.5 C 147.452,12.266 82.6184,53.266 37,124.5C 17.1801,159.453 5.34675,196.786 1.5,236.5C 1.5,158.167 1.5,79.8333 1.5,1.5C 78.1667,1.5 154.833,1.5 231.5,1.5 Z"/></g>
        <g><path style="opacity:1" fill="#2b2e31" d="M 231.5,1.5 C 247.167,1.5 262.833,1.5 278.5,1.5C 372.67,13.9824 441.504,62.3157 485,146.5C 497.333,173.709 505.167,202.043 508.5,231.5C 508.5,247.167 508.5,262.833 508.5,278.5C 495.413,376.079 444.413,445.912 355.5,488C 329.076,499.005 301.743,505.838 273.5,508.5C 261.167,508.5 248.833,508.5 236.5,508.5C 160.717,500.859 99.2166,467.193 52,407.5C 23.0978,367.366 6.26451,322.699 1.5,273.5C 1.5,261.167 1.5,248.833 1.5,236.5C 5.34675,196.786 17.1801,159.453 37,124.5C 82.6184,53.266 147.452,12.266 231.5,1.5 Z"/></g>
        <g><path style="opacity:1" fill="#fefefe" d="M 278.5,1.5 C 355.167,1.5 431.833,1.5 508.5,1.5C 508.5,78.1667 508.5,154.833 508.5,231.5C 505.167,202.043 497.333,173.709 485,146.5C 441.504,62.3157 372.67,13.9824 278.5,1.5 Z"/></g>
        <g><path style="opacity:1" fill="#fefefe" d="M 124.5,96.5 C 132.507,96.3336 140.507,96.5003 148.5,97C 150.081,98.828 151.415,100.828 152.5,103C 156.159,104.28 159.659,105.78 163,107.5C 161.895,131.963 157.395,155.796 149.5,179C 151.429,182.599 153.763,185.933 156.5,189C 167.209,195.927 178.876,198.927 191.5,198C 213.631,190.372 231.298,176.872 244.5,157.5C 242.883,155.368 242.383,153.035 243,150.5C 253.451,140.839 263.451,141.506 273,152.5C 274.171,154.842 275.338,157.176 276.5,159.5C 280.223,157.405 284.056,156.739 288,157.5C 295.028,167.028 301.861,176.695 308.5,186.5C 297.8,194.7 288.633,204.367 281,215.5C 273.846,230.63 268.513,246.296 265,262.5C 271.718,247.391 279.718,233.058 289,219.5C 295.133,212.034 302.466,206.034 311,201.5C 318.804,210.969 327.638,219.469 337.5,227C 340.738,231.908 344.905,235.741 350,238.5C 350.49,239.793 350.657,241.127 350.5,242.5C 351.552,242.351 352.552,242.517 353.5,243C 374.891,263.39 396.058,284.223 417,305.5C 423.203,314.246 427.536,323.913 430,334.5C 435.958,352.276 434.291,369.276 425,385.5C 422.293,389.035 418.793,390.202 414.5,389C 360.572,357.536 304.905,329.536 247.5,305C 245.5,302.92 243.5,300.92 241.5,299C 234.246,297.449 226.913,296.616 219.5,296.5C 203.371,298.327 187.204,299.661 171,300.5C 150.493,299.84 129.993,299.007 109.5,298C 100.904,296.785 93.4042,293.285 87,287.5C 84.4728,283.779 82.4728,279.779 81,275.5C 78.0658,261.967 76.7324,248.301 77,234.5C 77.5817,228.505 79.2484,222.838 82,217.5C 87.1,212.403 91.4333,206.736 95,200.5C 95.3333,198.167 95.6667,195.833 96,193.5C 99.1843,188.47 102.851,183.804 107,179.5C 109.725,172.384 112.725,165.384 116,158.5C 117.356,157.62 118.856,157.286 120.5,157.5C 118.501,144.504 116.501,131.504 114.5,118.5C 114.202,109.349 117.535,102.016 124.5,96.5 Z"/></g>
        <g><path style="opacity:1" fill="#3b3d40" d="M 250.5,149.5 C 258.219,149.694 264.219,153.027 268.5,159.5C 267.635,160.583 266.635,160.749 265.5,160C 261.613,156.889 257.28,154.556 252.5,153C 251.177,152.184 250.511,151.017 250.5,149.5 Z"/></g>
        <g><path style="opacity:1" fill="#fefefe" d="M 1.5,273.5 C 6.26451,322.699 23.0978,367.366 52,407.5C 99.2166,467.193 160.717,500.859 236.5,508.5C 158.167,508.5 79.8333,508.5 1.5,508.5C 1.5,430.167 1.5,351.833 1.5,273.5 Z"/></g>
        <g><path style="opacity:1" fill="#fefefe" d="M 508.5,278.5 C 508.5,355.167 508.5,431.833 508.5,508.5C 430.167,508.5 351.833,508.5 273.5,508.5C 301.743,505.838 329.076,499.005 355.5,488C 444.413,445.912 495.413,376.079 508.5,278.5 Z"/></g>
      </svg>
    </div>
    <div class="flex one jcenter">
      <label>
        <select id="selector" v-model="username_type" @change="selector_change">
          <option v-for="option in options" :key="option.value" :value="option.value">{{ option.text }}</option>
        </select>
      </label>
    </div>
    <div v-if="username_type == 'mobile'">
      <div class="flex one jcenter">
        <input id="mobile" autofocus type="tel" inputmode="numeric" pattern="\d{8}" placeholder="00000000" autocomplete="tel-local" @input="mobile_update" v-model="username" size="8" maxlength="8" required>
      </div>
    </div>
    <div v-if="username_type == 'email'">
      <div class="flex one jcenter email">
        <input id="email" autofocus type="email" placeholder="monkey@nkk.dk" autocomplete="email" v-model="username" required>
      </div>
      <div class="flex one jcenter email">
        <button @click="email_update">verify</button>
      </div>
    </div>
    <p>lockoff is synchronized with klubmodul about every hour - so if you just signed up or paid on klubmodul then wait an hour and try again</p>
    <div class="flex one">
      <div v-if="occupancy.currently < (occupancy.historical - 2)" style="text-align: center;">💚 less busy than usual (<span :title="occupancy.currently + ' checkins last hour where the average is ' + occupancy.historical + ' for this hour/day'">curr {{ occupancy.currently }} avg {{ occupancy.historical }}</span>)</div>
      <div v-if="(occupancy.currently >= (occupancy.historical -2)) & (occupancy.currently <= (occupancy.historical + 2))" style="text-align: center;">💛 average busyness (<span :title="occupancy.currently + ' checkins last hour where the average is ' + occupancy.historical + ' for this hour/day'">curr {{ occupancy.currently }} avg {{ occupancy.historical }}</span>)</div>
      <div v-if="occupancy.currently > (occupancy.historical + 2)" style="text-align: center;">🔥 more busy than usual (<span :title="occupancy.currently + ' checkins last hour where the average is ' + occupancy.historical + ' for this hour/day'">curr {{ occupancy.currently }} avg {{ occupancy.historical }}</span>)</div>
    </div>
  </div>
  <div v-show="step == 'totp'">
    <div class="flex one jcenter">
      <label for="pin">code</label>
    </div>
    <div class="flex one jcenter">
      <input id="otp" type="text" inputmode="numeric" pattern="\d{6}" placeholder="000000" autocomplete="one-time-code" @input="totp_update" v-model="totp" size="6" maxlength="6" required>
    </div>
    <div class="flex one jcenter">
      <p>if you did not receive a code then double check if your {{ username_type }} is set correct in nkk.klub-modul.dk and <a @click="tryagain">try again later (after about 2 hours as we sync klubmodul every two hours)</a></p>
    </div>
  </div>
</template>

<style scoped>
#selector {
  width: 8em;
}
div.email > input, div.email > button {
  font-size: 1.5em;
  margin-right: 1em;
  margin-left: 1em;
}
@media (min-width: 800px) {
  div.email > input, div.email > button {
    width: 50%;
  }
}
.jcenter {
  justify-content: center;
}
label {
  font-size: 1.5em;
  width: auto;
}
:where([autocomplete=tel-local]):focus, :where([autocomplete=one-time-code]):focus {
  border: none;
}
:where([autocomplete=tel-local]) {
  --otp-digits: 8;
  --otp-ls: 2ch;
  --otp-gap: 1.25;
  --otp-fz: 1.5em;
  --otp-ls: 1em;

  /* private consts */
  --_otp-bgsz: calc(var(--otp-ls) + 1ch);
  --_otp-digit: 0;

  all: unset;
  background: 
  linear-gradient(90deg, 
    var(--otp-bg, #BBB) calc(var(--otp-gap) * var(--otp-ls)),
    transparent 0),
    linear-gradient(90deg, 
    var(--otp-bg, #EEE) calc(var(--otp-gap) * var(--otp-ls)),
    transparent 0
  );
  background-position: calc(var(--_otp-digit) * var(--_otp-bgsz)) 0, 0 0;
  background-repeat: no-repeat, repeat-x;
  background-size: var(--_otp-bgsz) 100%;
  caret-color: var(--otp-cc, #222);
  caret-shape: block;
  clip-path: inset(0% calc(var(--otp-ls) / 2) 0% 0%);
  font-family: ui-monospace, monospace;
  font-size: var(--otp-fz, 2.5em);
  inline-size: calc(var(--otp-digits) * var(--_otp-bgsz));
  letter-spacing: var(--otp-ls);
  padding-block: var(--otp-pb, 1ch);
  padding-inline-start: calc(((var(--otp-ls) - 1ch) / 2) * var(--otp-gap));
}
:where([autocomplete=one-time-code]) {
  --otp-digits: 6;
  --otp-ls: 2ch;
  --otp-gap: 1.25;
  --otp-fz: 1.5em;
  --otp-ls: 1em;

  /* private consts */
  --_otp-bgsz: calc(var(--otp-ls) + 1ch);
  --_otp-digit: 0;

  all: unset;
  background: 
  linear-gradient(90deg, 
    var(--otp-bg, #BBB) calc(var(--otp-gap) * var(--otp-ls)),
    transparent 0),
    linear-gradient(90deg, 
    var(--otp-bg, #EEE) calc(var(--otp-gap) * var(--otp-ls)),
    transparent 0
  );
  background-position: calc(var(--_otp-digit) * var(--_otp-bgsz)) 0, 0 0;
  background-repeat: no-repeat, repeat-x;
  background-size: var(--_otp-bgsz) 100%;
  caret-color: var(--otp-cc, #222);
  caret-shape: block;
  clip-path: inset(0% calc(var(--otp-ls) / 2) 0% 0%);
  font-family: ui-monospace, monospace;
  font-size: var(--otp-fz, 2.5em);
  inline-size: calc(var(--otp-digits) * var(--_otp-bgsz));
  letter-spacing: var(--otp-ls);
  padding-block: var(--otp-pb, 1ch);
  padding-inline-start: calc(((var(--otp-ls) - 1ch) / 2) * var(--otp-gap));
}

#logo {
  width: 40%;
  margin: 0;
  padding:0 0 3em 0;
  margin-right: auto;
  margin-left: auto;
}
</style>
