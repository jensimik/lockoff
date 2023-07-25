export const getMobileOS = () => {
    const ua = navigator.userAgent
    if (/android/i.test(ua)) {
      return "Android"
    }
    else if (/iPhone/i.test(ua)) {
      return "iOS"
    }
    return "Other"
  }