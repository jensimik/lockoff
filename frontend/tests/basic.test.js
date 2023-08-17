// import Login from '../src/views/Login.vue'
import { expect, test } from 'vitest'
import allMethods from '../src/api/resources/allMethods'

const mockValue = {};

test('login', async () => {
    // first some sanity checks if component exists and api resource exists
    // expect(Login).toBeTruthy();
    expect(allMethods).toBeTruthy();
})