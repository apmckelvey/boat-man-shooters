vertex_shader = '''
#version 330 core

in vec2 in_vert;
out vec2 v_uv;
out vec2 v_world_pos;

uniform vec2 viewportSize;
uniform vec2 cameraPos;

void main() {
    v_uv = in_vert * 0.5 + 0.5;
    v_world_pos = in_vert * viewportSize * 0.5 + cameraPos;
    gl_Position = vec4(in_vert, 0.0, 1.0);
}
'''

fragment_shader = '''
#version 330 core
precision highp float;

uniform float time;
uniform vec2 boatPosition;
uniform float boatRotation;
uniform vec2 boatVelocity;
uniform float wakeFade;
uniform sampler2D boatTexture;
uniform sampler2D enemyTexture;
uniform int numOtherPlayers;
uniform float otherBoatPositions[20];
uniform float otherBoatRotations[10];
uniform float otherBoatSpeeds[10];
uniform float otherBoatSwayPhases[10];
uniform float otherBoatSwayAmps[10];
uniform vec2 worldSize;
uniform float boatAspect;

// Item uniforms
uniform int numItems;
uniform float itemPositions[30];
uniform int itemTypes[15];
uniform sampler2D itemTexture1;
uniform sampler2D itemTexture2;
uniform sampler2D itemTexture3;
uniform sampler2D itemTexture4;
uniform sampler2D itemTexture5;

in vec2 v_uv;
in vec2 v_world_pos;
out vec4 fragColor;

const float BOAT_SIZE = 0.15;
const float ITEM_SIZE = 0.3;
const float BORDER_WIDTH = 0.3;
const float BORDER_FADE = 0.5;

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453);
}
float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash(i);
    float b = hash(i + vec2(1.0,0.0));
    float c = hash(i + vec2(0.0,1.0));
    float d = hash(i + vec2(1.0,1.0));
    return mix(mix(a,b,f.x), mix(c,d,f.x), f.y);
}
float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    float f = 1.0;
    for(int i=0;i<6;i++){
        v += a * noise(p * f);
        f *= 2.0;
        a *= 0.5;
    }
    return v;
}
vec2 rotate2D(vec2 p, float angle) {
    float c = cos(angle);
    float s = sin(angle);
    return vec2(p.x * c - p.y * s, p.x * s + p.y * c);
}

float getDistanceFromBoundary(vec2 pos, vec2 worldSize) {
    float distLeft = pos.x;
    float distRight = worldSize.x - pos.x;
    float distBottom = pos.y;
    float distTop = worldSize.y - pos.y;
    return min(min(distLeft, distRight), min(distBottom, distTop));
}

float unifiedRipples(vec2 p, vec2 boatPos, float t, float speed) {
    float dist = length(p - boatPos);
    float ripple1 = sin(dist * 38.0 - t * 2.8) * 0.5 + 0.5;
    float ripple2 = sin(dist * 48.0 - t * 3.3 + 1.2) * 0.5 + 0.5;
    float ripple3 = sin(dist * 28.0 - t * 2.2 + 2.5) * 0.5 + 0.5;
    float ripple4 = sin(dist * 58.0 - t * 4.1 + 3.7) * 0.5 + 0.5;
    float base = ripple1 * 0.35 + ripple2 * 0.25 + ripple3 * 0.25 + ripple4 * 0.15;
    base += noise(p * 100.0 + t * 1.5) * 0.15;
    base += noise(p * 200.0 + t * 2.0) * 0.08;
    float fade = smoothstep(0.28, 0.0, dist);
    return base * fade * mix(0.5, 0.35, smoothstep(0.0, 0.5, speed));
}

float wakePattern(vec2 p, vec2 boatPos, float boatRot, float speed, float t) {
    vec2 localP = p - boatPos;
    localP = rotate2D(localP, boatRot);
    float dist = length(localP);
    float frontFade = smoothstep(0.02, -0.12, localP.x);
    float wakeAngle = abs(localP.y / (abs(localP.x) + 0.01));
    float wakeShape = smoothstep(0.6, 0.0, wakeAngle);

    float ripples = sin(dist * 25.0 - t * 5.0) * 0.3;
    ripples += sin(dist * 35.0 - t * 6.5 + 1.5) * 0.2;
    ripples += sin(dist * 45.0 - t * 7.0 + 3.0) * 0.15;
    ripples += noise(localP * 60.0 + t * 1.5) * 0.12;
    ripples += noise(localP * 120.0 + t * 2.5) * 0.08;

    float foam = smoothstep(0.65, 0.9, ripples) * 0.4;
    float turbulence = fbm(localP * 80.0 + t * 2.0) * 0.2;
    foam += smoothstep(0.7, 0.95, turbulence) * 0.25;

    float distanceFade = smoothstep(0.3, 0.0, dist);
    return (wakeShape * 0.35 + (ripples * 0.3 + foam * 0.4)) * distanceFade * frontFade * speed * 0.5;
}

float bowWave(vec2 p, vec2 boatPos, float boatRot, float speed, float t) {
    vec2 localP = p - boatPos;
    localP = rotate2D(localP, boatRot);
    float dist = length(localP);
    float backFade = smoothstep(-0.02, 0.12, localP.x);

    float wave = sin(dist * 30.0 - t * 8.0) * 0.5 + 0.5;
    wave += sin(dist * 40.0 - t * 10.0 + 1.5) * 0.2;
    wave += sin(dist * 50.0 - t * 12.0 + 2.5) * 0.15;
    wave += sin(abs(atan(localP.y, localP.x)) * 12.0 + t * 4.0) * 0.15;

    wave += noise(localP * 70.0 + t * 3.0) * 0.15;
    wave += noise(localP * 140.0 + t * 4.0) * 0.08;

    return wave * smoothstep(0.15, 0.0, dist) * backFade * 0.3 * speed;
}

vec3 posterizeColor(vec3 color, float levels) {
    return floor(color * levels) / levels;
}

void main() {
    vec2 pos = v_world_pos * 3.0;
    float swayX = sin(time * 1.2) * 0.008;
    float swayY = sin(time * 2.0) * 0.012;
    float swayRotation = sin(time * 1.5) * 0.08;
    vec2 boatPos = boatPosition + vec2(swayX, swayY);
    float boatSpeed = length(boatVelocity);

    float wave1 = fbm(pos + vec2(time * 0.2, time * 0.15));
    float wave2 = fbm(pos * 1.3 - vec2(time * 0.15, time * 0.25));
    float wave3 = fbm(pos * 1.8 + vec2(time * 0.08, -time * 0.2));
    float wave4 = fbm(pos * 2.5 + vec2(time * 0.12, time * 0.18));
    float wave5 = fbm(pos * 3.2 - vec2(time * 0.1, -time * 0.15));

    float waves = (wave1 + wave2 * 0.6 + wave3 * 0.4 + wave4 * 0.3 + wave5 * 0.2) / 2.5;

    float caustics = sin(pos.x * 10.0 + time * 1.5) * sin(pos.y * 10.0 + time * 1.8);
    caustics += sin(pos.x * 15.0 - time * 2.0) * sin(pos.y * 15.0 + time * 2.2);
    waves += caustics * 0.03;

    waves += unifiedRipples(v_world_pos, boatPos, time, boatSpeed);
    float wakeStrength = smoothstep(0.0, 0.2, boatSpeed) * wakeFade * 0.6;
    waves += (wakePattern(v_world_pos, boatPos, -boatRotation, boatSpeed * 3.0, time)
             + bowWave(v_world_pos, boatPos, -boatRotation, boatSpeed * 2.5, time)) * wakeStrength;

    for (int i = 0; i < numOtherPlayers; i++) {
        int idx = i * 2;
        vec2 othPos = vec2(otherBoatPositions[idx], otherBoatPositions[idx+1]);
        float othRot = otherBoatRotations[i];
        float othSpeed = otherBoatSpeeds[i];
        float phase = otherBoatSwayPhases[i];
        float amp = otherBoatSwayAmps[i];
        vec2 sway = vec2(sin(time * 1.2 + phase) * (0.008 * amp), sin(time * 2.0 + phase*1.37) * (0.012 * amp));
        vec2 othPosSway = othPos + sway;
        waves += unifiedRipples(v_world_pos, othPosSway, time, othSpeed) * 0.9;
        waves += wakePattern(v_world_pos, othPosSway, -othRot, othSpeed * 2.5, time) * 0.75;
    }

    waves = floor(waves * 16.0) / 16.0;

    vec3 deepWater = vec3(0.02, 0.18, 0.35);
    vec3 darkWater = vec3(0.06, 0.32, 0.52);
    vec3 midWater = vec3(0.14, 0.50, 0.68);
    vec3 lightWater = vec3(0.28, 0.68, 0.82);
    vec3 brightWater = vec3(0.48, 0.82, 0.92);
    vec3 foamColor = vec3(0.92, 0.96, 0.98);

    vec3 waterColor;
    if (waves < 0.15) {
        waterColor = mix(deepWater, darkWater, waves / 0.15);
    } else if (waves < 0.35) {
        waterColor = mix(darkWater, midWater, (waves - 0.15) / 0.20);
    } else if (waves < 0.55) {
        waterColor = mix(midWater, lightWater, (waves - 0.35) / 0.20);
    } else if (waves < 0.75) {
        waterColor = mix(lightWater, brightWater, (waves - 0.55) / 0.20);
    } else {
        waterColor = mix(brightWater, foamColor, (waves - 0.75) / 0.25);
    }

    waterColor = posterizeColor(waterColor, 32.0);

    float depthModulation = fbm(v_world_pos * 5.0 + time * 0.05) * 0.12;
    waterColor = mix(waterColor, deepWater, depthModulation * 0.25);

    float specular = pow(max(0.0, waves - 0.65), 4.0) * 0.35;
    waterColor += vec3(specular);

    float distFromBoundary = getDistanceFromBoundary(v_world_pos, worldSize);

    if (distFromBoundary < BORDER_WIDTH) {
        float borderIntensity = smoothstep(BORDER_WIDTH, 0.0, distFromBoundary);
        float pulse = sin(time * 3.0) * 0.3 + 0.7;
        vec3 boundaryColor = vec3(0.8, 0.15, 0.1);
        vec3 warningColor = vec3(0.9, 0.4, 0.2);
        vec3 edgeColor = mix(warningColor, boundaryColor, borderIntensity);
        waterColor = mix(waterColor, edgeColor, borderIntensity * 0.6 * pulse);

        if (distFromBoundary < BORDER_WIDTH * 0.5) {
            float stripePattern = step(0.5, fract(distFromBoundary * 15.0 + time * 2.0));
            waterColor = mix(waterColor, vec3(1.0, 0.2, 0.1), stripePattern * borderIntensity * 0.4);
        }
    }

    if (distFromBoundary < BORDER_WIDTH + BORDER_FADE) {
        float fadeIntensity = smoothstep(BORDER_WIDTH + BORDER_FADE, BORDER_WIDTH, distFromBoundary);
        waterColor = mix(waterColor, vec3(0.9, 0.4, 0.2) * 0.6, fadeIntensity * 0.2);
    }

    // Draw items BEFORE boats so boats appear on top
    for (int i = 0; i < numItems && i < 15; i++) {
        int idx = i * 2;
        vec2 itemPos = vec2(itemPositions[idx], itemPositions[idx+1]);

        vec2 itemUV = v_world_pos - itemPos;
        vec2 itemTex = (itemUV / ITEM_SIZE) + 0.5;

        if (itemTex.x >= 0.0 && itemTex.x <= 1.0 && itemTex.y >= 0.0 && itemTex.y <= 1.0) {
            vec4 itemColor = vec4(0.0);
            int itemType = itemTypes[i];

            if (itemType == 1) itemColor = texture(itemTexture1, itemTex);
            else if (itemType == 2) itemColor = texture(itemTexture2, itemTex);
            else if (itemType == 3) itemColor = texture(itemTexture3, itemTex);
            else if (itemType == 4) itemColor = texture(itemTexture4, itemTex);
            else if (itemType == 5) itemColor = texture(itemTexture5, itemTex);

            if (itemColor.a > 0.05) {
                waterColor = mix(waterColor, itemColor.rgb, itemColor.a);
            }
        }
    }

    vec2 boatUV = v_world_pos - boatPos;
    boatUV = rotate2D(boatUV, -boatRotation + swayRotation);
    vec2 boatTex = vec2(boatUV.x / (BOAT_SIZE * boatAspect), boatUV.y / BOAT_SIZE) + 0.5;
    if (boatTex.x >= 0.0 && boatTex.x <= 1.0 && boatTex.y >= 0.0 && boatTex.y <= 1.0) {
        vec4 bc = texture(boatTexture, boatTex);
        if (bc.a > 0.05) waterColor = mix(waterColor, bc.rgb, bc.a);
    }

    for (int i = 0; i < numOtherPlayers; i++) {
        int idx = i * 2;
        vec2 othPos = vec2(otherBoatPositions[idx], otherBoatPositions[idx+1]);
        float othRot = otherBoatRotations[i];
        float phase = otherBoatSwayPhases[i];
        float amp = otherBoatSwayAmps[i];
        vec2 sway = vec2(sin(time * 1.2 + phase) * (0.008 * amp), sin(time * 2.0 + phase*1.37) * (0.012 * amp));
        vec2 othPosSway = othPos + sway;
        vec2 othUV = v_world_pos - othPosSway;
        othUV = rotate2D(othUV, -othRot);
        vec2 othTex = vec2(othUV.x / (BOAT_SIZE * boatAspect), othUV.y / BOAT_SIZE) + 0.5;
        if (othTex.x >= 0.0 && othTex.x <= 1.0 && othTex.y >= 0.0 && othTex.y <= 1.0) {
            vec4 oc = texture(enemyTexture, othTex);
            if (oc.a > 0.05) {
                vec3 tint = vec3(1.0, 1.0, 1.0);
                waterColor = mix(waterColor, oc.rgb * tint, 1.0);
            }
        }
    }

    fragColor = vec4(waterColor, 1.0);
}
'''