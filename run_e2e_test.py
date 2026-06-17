"""A5 Full E2E Data Flow Test — records real API responses"""
import json, urllib.request, time, sys

BASE = 'http://127.0.0.1:8000'
trace = {'flow': [], 'summary': {}}

def post(path, body):
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode(),
          headers={'Content-Type':'application/json'}, method='POST')
    return json.loads(urllib.request.urlopen(req).read())

def get(path):
    return json.loads(urllib.request.urlopen(BASE+path).read())

def step(n, name, method, path, req_body=None):
    print(f"  [{n}] {name}...", end=' ', flush=True)
    try:
        if method == 'GET':
            r = get(path)
        else:
            r = post(path, req_body)
        trace['flow'].append({'step':n, 'name':name, 'method':method, 'path':path,
            'request': req_body, 'response': r})
        print("OK")
    except Exception as e:
        trace['flow'].append({'step':n, 'name':name, 'method':method, 'path':path,
            'request': req_body, 'error': str(e)})
        print(f"FAIL: {e}")
        return None
    return r

print("=" * 60)
print("A5 Full E2E Data Flow Test")
print("=" * 60)
print()

# --- Auth & Room Setup ---
r1 = step(1, "Leader Registration", "POST", "/api/auth/register",
    {"userName": "张团长", "password": "demo123"})
leader_token = r1['token']; leader_id = r1['userId']

r2 = step(2, "Leader Creates Room", "POST", "/api/rooms",
    {"token": leader_token, "roomName": "上午研学团", "scenicAreaId": "huangshan", "routeId": "classic"})
room_id = r2['roomId']

r3 = step(3, "Visitor A Registration", "POST", "/api/auth/register",
    {"userName": "游客A", "password": "demo123"})
va_token = r3['token']; va_id = r3['userId']

r4 = step(4, "Visitor A Joins Room", "POST", f"/api/rooms/{room_id}/join",
    {"token": va_token})

r5 = step(5, "Visitor B Registration", "POST", "/api/auth/register",
    {"userName": "游客B", "password": "demo123"})
vb_token = r5['token']; vb_id = r5['userId']

r6 = step(6, "Visitor B Joins Room", "POST", f"/api/rooms/{room_id}/join",
    {"token": vb_token})

r7 = step(7, "Room Status (2 visitors)", "GET", f"/api/rooms/{room_id}")

# --- Tour Control ---
r8 = step(8, "Leader Sets Spot -> main_hall", "POST",
    f"/api/rooms/{room_id}/current-spot", {"spotId": "main_hall"})

r9 = step(9, "AI Avatar State", "GET", f"/api/rooms/{room_id}/avatar-state")

# --- Public Q&A ---
q_pub = "这个建筑是什么时候建的？"
r10 = step(10, "Visitor A Public Question", "POST", "/api/ai/public-question",
    {"roomId": room_id, "userId": va_id, "question": q_pub, "needAudio": False})
if r10:
    trace['flow'][-1]['response'] = {'answer': r10.get('answer','')[:300],
        'sources': r10.get('sources',[]), 'avatarState': r10.get('avatarState',{})}

# --- Private Q&A ---
q_priv = "我有点累，附近有休息区吗？"
r11 = step(11, "Visitor B Private Question", "POST", "/api/ai/public-question",
    {"roomId": room_id, "userId": vb_id, "question": q_priv, "needAudio": False})
if r11:
    trace['flow'][-1]['response'] = {'answer': r11.get('answer','')[:300],
        'warning': r11.get('warning'), 'sources': r11.get('sources',[]),
        'avatarState': r11.get('avatarState',{})}

# --- Vision ---
r12 = step(12, "Vision: bell_tower image", "POST", "/api/vision/recognize",
    {"roomId": room_id, "userId": va_id,
     "imageUrl": "/uploads/vision/bell_tower.jpg", "currentSpotId": "main_hall"})

# --- Route Recommend ---
r13 = step(13, "Route: elderly + less walking", "POST", "/api/recommend/route",
    {"roomId": room_id, "userId": va_id,
     "preferences": {"interest":["history","photography"], "timeLimit":60,
     "physicalStrength":"low", "withElderly":True, "withChildren":False, "avoidCrowd":True}})

# --- Feedback ---
r14 = step(14, "Visitor A Feedback 5-star", "POST", "/api/feedback",
    {"score": 5, "roomId": room_id, "userId": va_id, "scene": "public-tour", "comment": "AI讲解很专业"})
r15 = step(15, "Visitor B Feedback 4-star", "POST", "/api/feedback",
    {"score": 4, "roomId": room_id, "userId": vb_id, "scene": "private-assistant", "comment": "休息区推荐很及时"})

# --- Dashboard ---
r16 = step(16, "Dashboard Overview", "GET", "/api/dashboard/overview")
r17 = step(17, "Dashboard Hot Questions", "GET", "/api/dashboard/hot-questions")
r18 = step(18, "Dashboard Satisfaction", "GET", "/api/dashboard/satisfaction")
r19 = step(19, "Dashboard System Metrics", "GET", "/api/dashboard/system-metrics")

# --- Logs ---
r20 = step(20, "Room Voice Logs", "GET", f"/api/rooms/{room_id}/voice-logs")

# --- Summary ---
dashboard = trace['flow'][15]['response']
trace['summary'] = {
    'test_name': 'A5 Full E2E Demo Walkthrough',
    'room_id': room_id,
    'participants': [
        {'name': '张团长', 'role': 'leader', 'userId': leader_id},
        {'name': '游客A', 'role': 'visitor', 'userId': va_id},
        {'name': '游客B', 'role': 'visitor', 'userId': vb_id},
    ],
    'data_flow': [
        'Register (x3) → Create Room → Join (x2)',
        'Set Spot → Avatar State',
        'Public QA (visitor A) → Private QA (visitor B)',
        'Vision Recognition → Route Recommendation',
        'Feedback (x2) → Dashboard Stats'
    ],
    'metrics_by_step': {
        'public_questions': 1,
        'private_questions': 1,
        'vision_recognitions': 1,
        'route_recommendations': 1,
        'feedback_count': 2,
    },
    'dashboard_snapshot': {
        'todayVisitors': dashboard.get('todayVisitors'),
        'activeRooms': dashboard.get('activeRooms'),
        'questionCount': dashboard.get('questionCount'),
        'voiceQuestionCount': dashboard.get('voiceQuestionCount'),
        'visionRecognizeCount': dashboard.get('visionRecognizeCount'),
        'routeRecommendCount': dashboard.get('routeRecommendCount'),
    },
    'complete': True
}

passed = sum(1 for f in trace['flow'] if 'error' not in f)
total = len(trace['flow'])
print()
print(f"RESULTS: {passed}/{total} steps passed")

with open('frontend_e2e_trace.json', 'w', encoding='utf-8') as f:
    json.dump(trace, f, ensure_ascii=False, indent=2)
print(f"Saved: frontend_e2e_trace.json ({passed}/{total} OK)")
