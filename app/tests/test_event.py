import modules.event as event
import json
import unittest


class TestEventAttendingAccepted(unittest.TestCase):
    def setUp(self):
        self.event = json.loads("/fixtures/event_attending_accepted.json")
        
    
    def test_get_self_from_attendees(self):
        response = {
            "email": "michael.bifolco@ordergroove.com",
            "displayName": "Michael Bifolco",
            "self": True,
            "responseStatus": "accepted"
        }
        attendee_self = event.get_self_from_attendees(self.event)
        print (attendee_self)
        self.assertDictEqual(response, attendee_self)

if __name__ == '__main__':
    unittest.main()

 
