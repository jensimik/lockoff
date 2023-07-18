import { APISettings } from '../config.js';

export default {

    async request_totp(mobile) {
        const response = await fetch(APISettings.baseURL + '/request-totp', {
            method: 'POST',
            headers: { ...APISettings.headers, 'Content-Type': 'Application/json' },
            body: JSON.stringify({mobile: mobile})
        });
        if (response.status != 200) {
            throw response.status;
        } else {
            return response.json();
        }
    },
    async login(mobile, code) {
        let formData = new FormData();
        formData.append('username', mobile);
        formData.append('password', code);
        const response = await fetch(APISettings.baseURL + '/login', {
            method: 'POST',
            headers: APISettings.headers,
            body: formData
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