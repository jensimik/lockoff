import { APISettings } from '../config.js';

export default {

    async request_totp(data) {
        const response = await fetch(APISettings.baseURL + '/request_totp', {
            method: 'POST',
            headers: APISettings.headers,
            body: JSON.stringify(data)
        });
        if (response.status != 200) {
            throw response.status;
        } else {
            return response.json();
        }
    },
    async login(data) {
        const response = await fetch(APISettings.baseURL + '/login', {
            method: 'POST',
            headers: APISettings.headers,
            body: JSON.stringify(data)
        });
        if (response.status != 200) {
            throw response.status;
        } else {
            return response.json();
        }
    },
    async get_me(token) {
        const response = await fetch(APISettings.baseURL + '/me?token=' + token, {
            method: 'GET',
            headers: APISettings.headers
        });
        if (response.status != 200) {
            throw response.status;
        } else {
            return response.json();
        }
    },
}