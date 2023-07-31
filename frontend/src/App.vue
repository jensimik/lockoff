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
    width: 100%;
    max-width: 800px;
}
</style>