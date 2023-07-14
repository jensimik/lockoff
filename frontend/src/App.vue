<script setup>
import otp from './components/OTP.vue';
import { ref } from 'vue';


var phone = ref();
var show_pin = ref(false);

const update = async(e) => {
  console.log(e);
  show_pin.value = true;

}


</script>

<template>
  <div>
    <p id="mobileemoji">📱</p>
    <div class="flex one">
      <label for="mobile">Verify mobile number</label>
      <otp :digit-count="8" :placeholder="0" :nameid="mobile" @update:otp="update"></otp>
    </div>
    <div v-show="show_pin">
      <div class="flex one">
        <label for="pin">SMS code</label>
     </div>
     <div class="flex one">
       <otp :digit-count="6" :placeholder="1" :nameid="pin" @update:otp="update"></otp>
     </div>
    </div>
  </div>
</template>

<style scoped>
#mobileemoji {
  font-size: 10em;
  margin:0;
  padding:0;
}
</style>
