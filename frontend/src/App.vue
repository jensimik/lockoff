<script setup>
import { RouterView } from 'vue-router';
</script>

<template>
    <div id="wrap">
        <RouterView />
    </div>
</template>

<style scoped>
#wrap {
    width: 100vw;
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
}
@media print { 
    #wrap {
        width: unset;
        max-width: unset;
    }
}
</style>