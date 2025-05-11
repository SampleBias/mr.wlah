/*
MongoDB Schema for Mr. Wlah Application

This is a demonstration of the MongoDB schema that would be used
in a full implementation with a Node.js backend.

In a real implementation, this would be connected to a MongoDB database
and used with Mongoose or a similar ODM.
*/

// User Schema
const UserSchema = {
    _id: ObjectId,
    auth0Id: String,              // Auth0 user ID
    email: String,                // User's email from Auth0
    name: String,                 // User's name from Auth0
    createdAt: Date,              // When the user first signed up
    lastLogin: Date,              // Last time the user logged in
    usageCount: Number,           // Number of transformations performed
    preferences: {                // User preferences
        defaultTone: String,      // Default tone preference
        saveHistory: Boolean      // Whether to save transformation history
    }
};

// Transformation History Schema
const TransformationSchema = {
    _id: ObjectId,
    userId: ObjectId,             // Reference to user who created this transformation
    originalText: String,         // The original AI-generated text
    transformedText: String,      // The humanized text output
    tone: String,                 // The tone used for transformation
    createdAt: Date,              // When the transformation was created
    metadata: {                   // Additional metadata
        characterCount: Number,   // Length of original text
        sourceType: String        // How the text was input (paste, upload)
    }
};

// API Usage Stats Schema
const ApiUsageSchema = {
    _id: ObjectId,
    userId: ObjectId,             // Reference to user
    date: Date,                   // Date of API usage
    callCount: Number,            // Number of API calls made
    characterCount: Number,       // Total characters processed
    successCount: Number,         // Number of successful transformations
    errorCount: Number            // Number of failed transformations
};

// Example MongoDB Indexes
/*
db.users.createIndex({ "auth0Id": 1 }, { unique: true });
db.users.createIndex({ "email": 1 });
db.transformations.createIndex({ "userId": 1 });
db.transformations.createIndex({ "createdAt": -1 });
db.apiUsage.createIndex({ "userId": 1, "date": 1 });
*/

// Example MongoDB Queries

// Get all transformations for a user
/*
db.transformations.find({ userId: ObjectId("user_id_here") })
                  .sort({ createdAt: -1 })
                  .limit(10);
*/

// Get usage statistics for a user over the last 30 days
/*
db.apiUsage.aggregate([
    { $match: { 
        userId: ObjectId("user_id_here"),
        date: { $gte: new Date(Date.now() - 30*24*60*60*1000) }
    }},
    { $group: {
        _id: null,
        totalCalls: { $sum: "$callCount" },
        totalCharacters: { $sum: "$characterCount" },
        avgSuccessRate: { $avg: { $divide: ["$successCount", { $add: ["$successCount", "$errorCount"] }] } }
    }}
]);
*/

// Get most popular tone choices across all users
/*
db.transformations.aggregate([
    { $group: {
        _id: "$tone",
        count: { $sum: 1 }
    }},
    { $sort: { count: -1 }},
    { $limit: 5 }
]);
*/ 