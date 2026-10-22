/* Everything below is read with no permission prompt, from any page, the
 * moment it loads. None of it is a vulnerability - it is the ordinary web
 * platform, which is the uncomfortable part. */
(function () {
    var d = {
        screen:    screen.width + 'x' + screen.height,
        window:    innerWidth + 'x' + innerHeight,
        timezone:  (Intl.DateTimeFormat().resolvedOptions() || {}).timeZone || '',
        languages: (navigator.languages || []).join(','),
        cores:     navigator.hardwareConcurrency || '',
        memory:    navigator.deviceMemory || '',
        touch:     navigator.maxTouchPoints || 0,
        platform:  (navigator.userAgentData && navigator.userAgentData.platform)
                   || navigator.platform || ''
    };
    var body = JSON.stringify(d);
    try {
        navigator.sendBeacon('/collect', new Blob([body], { type: 'application/json' }));
    } catch (e) {
        var x = new XMLHttpRequest();
        x.open('POST', '/collect', true);
        x.setRequestHeader('Content-Type', 'application/json');
        x.send(body);
    }
})();
