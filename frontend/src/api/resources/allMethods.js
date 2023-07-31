import { APISettings } from '../config.js';
import { getWithExpiry } from '../../store.js';

export default {

    async request_totp(username, username_type) {
        const response = await fetch(APISettings.baseURL + '/request-totp', {
            method: 'POST',
            headers: { ...APISettings.headers, 'Content-Type': 'Application/json' },
            body: JSON.stringify({username: username, username_type: username_type})
        });
        if (response.status != 200) {
            throw response.status;
        } else {
            return response.json();
        }
    },
    async login(username, username_type, totp) {
        const response = await fetch(APISettings.baseURL + '/login', {
            method: 'POST',
            headers: { ...APISettings.headers, 'Content-Type': 'Application/json' },
            body: JSON.stringify({username: username, username_type: username_type, totp: totp})
        });
        if (response.status != 200) {
            throw response.status;
        } else {
            return response.json();
        }
    },
    async get_me() {
        var access_token = getWithExpiry("access_token");
        const response = await fetch(APISettings.baseURL + '/me', {
            method: 'GET',
            headers: {...APISettings.headers, Authorization: "Bearer " + access_token}
        });
        if (response.status != 200) {
            throw response.status;
        } else {
            return response.json();
        }
    },
    async system_status() {
        var access_token = getWithExpiry("access_token");
        const response = await fetch(APISettings.baseURL + '/admin/system-status', {
            method: 'GET',
            headers: {...APISettings.headers, Authorization: "Bearer " + access_token}
        });
        if (response.status != 200) {
            throw response.status;
        } else {
            return response.json();
        }
    },
    async klubmodul_force_resync() {
        var access_token = getWithExpiry("access_token");
        const response = await fetch(APISettings.baseURL + '/admin/klubmodul-force-resync', {
            method: 'POST',
            headers: {...APISettings.headers, Authorization: "Bearer " + access_token}
        });
        if (response.status != 200) {
            throw response.status;
        } else {
            return response.json();
        }
    },
}