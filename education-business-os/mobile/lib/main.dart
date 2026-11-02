import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();
  runApp(const AptivernStudentApp());
}

class AptivernStudentApp extends StatelessWidget {
  const AptivernStudentApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'Aptivern Student Portal',
        theme: ThemeData(
          colorSchemeSeed: const Color(0xFF176B43),
          useMaterial3: true,
        ),
        home: const AuthGate(),
      );
}

class AuthGate extends StatelessWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context) => StreamBuilder<User?>(
        stream: FirebaseAuth.instance.authStateChanges(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Scaffold(
              body: Center(child: CircularProgressIndicator()),
            );
          }
          if (!snapshot.hasData) return const SignInScreen();
          return const StudentHomeScreen();
        },
      );
}

class SignInScreen extends StatefulWidget {
  const SignInScreen({super.key});

  @override
  State<SignInScreen> createState() => _SignInScreenState();
}

class _SignInScreenState extends State<SignInScreen> {
  final email = TextEditingController();
  final password = TextEditingController();
  String? error;
  bool busy = false;

  Future<void> signIn() async {
    setState(() {
      busy = true;
      error = null;
    });
    try {
      await FirebaseAuth.instance.signInWithEmailAndPassword(
        email: email.text.trim(),
        password: password.text,
      );
    } on FirebaseAuthException catch (e) {
      setState(() => error = e.message ?? e.code);
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  void dispose() {
    email.dispose();
    password.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Aptivern Student Portal')),
        body: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    'Your learning, in one place',
                    style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 20),
                  TextField(
                    controller: email,
                    keyboardType: TextInputType.emailAddress,
                    decoration: const InputDecoration(labelText: 'Email'),
                  ),
                  TextField(
                    controller: password,
                    obscureText: true,
                    decoration: const InputDecoration(labelText: 'Password'),
                  ),
                  if (error != null)
                    Padding(
                      padding: const EdgeInsets.all(8),
                      child: Text(
                        error!,
                        style: const TextStyle(color: Colors.red),
                      ),
                    ),
                  const SizedBox(height: 16),
                  FilledButton(
                    onPressed: busy ? null : signIn,
                    child: Text(busy ? 'Signing in…' : 'Sign in'),
                  ),
                ],
              ),
            ),
          ),
        ),
      );
}

class StudentHomeScreen extends StatefulWidget {
  const StudentHomeScreen({super.key});

  @override
  State<StudentHomeScreen> createState() => _StudentHomeScreenState();
}

class _StudentHomeScreenState extends State<StudentHomeScreen> {
  String? selectedOrganizationId;

  @override
  Widget build(BuildContext context) {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) return const SignInScreen();

    // This directory contains only organizations linked to the signed-in user.
    // Its Firestore rules permit the user to list only their own membership index.
    final memberships = FirebaseFirestore.instance
        .collection('userOrganizationMemberships')
        .doc(user.uid)
        .collection('organizations')
        .where('status', isEqualTo: 'active')
        .snapshots();

    return StreamBuilder<QuerySnapshot<Map<String, dynamic>>>(
      stream: memberships,
      builder: (context, membershipSnapshot) {
        if (membershipSnapshot.hasError) {
          return _messageScaffold(
            'Unable to load your organization memberships. Please try again.',
          );
        }
        if (!membershipSnapshot.hasData) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }

        final studentMemberships = membershipSnapshot.data!.docs
            .where((doc) => doc.data()['role'] == 'student')
            .toList();

        if (studentMemberships.isEmpty) {
          return Scaffold(
            appBar: AppBar(
              title: const Text('My Learning'),
              actions: [_signOutButton()],
            ),
            body: const Center(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: Text(
                  'No active student workspace was found. Ask your school administrator to add you as a student.',
                  textAlign: TextAlign.center,
                ),
              ),
            ),
          );
        }

        final hasSelected = studentMemberships.any(
          (doc) => doc.id == selectedOrganizationId,
        );
        final currentOrganizationId =
            hasSelected ? selectedOrganizationId! : studentMemberships.first.id;

        if (!hasSelected) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (mounted && selectedOrganizationId != currentOrganizationId) {
              setState(() => selectedOrganizationId = currentOrganizationId);
            }
          });
        }

        final currentMembership = studentMemberships.firstWhere(
          (doc) => doc.id == currentOrganizationId,
        );
        final organizationName =
            currentMembership.data()['organizationName']?.toString() ??
                currentOrganizationId;

        return Scaffold(
          appBar: AppBar(
            title: const Text('My Learning'),
            actions: [
              if (studentMemberships.length > 1)
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 8),
                  child: DropdownButtonHideUnderline(
                    child: DropdownButton<String>(
                      value: currentOrganizationId,
                      icon: const Icon(Icons.expand_more),
                      items: studentMemberships.map((doc) {
                        final data = doc.data();
                        final name =
                            data['organizationName']?.toString() ?? doc.id;
                        return DropdownMenuItem<String>(
                          value: doc.id,
                          child: Text(name, overflow: TextOverflow.ellipsis),
                        );
                      }).toList(),
                      onChanged: (value) {
                        if (value != null) {
                          setState(() => selectedOrganizationId = value);
                        }
                      },
                    ),
                  ),
                ),
              _signOutButton(),
            ],
          ),
          body: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                child: Card(
                  child: ListTile(
                    leading: const Icon(Icons.school),
                    title: Text(organizationName),
                    subtitle: Text('Workspace: $currentOrganizationId'),
                  ),
                ),
              ),
              Expanded(
                child: StreamBuilder<QuerySnapshot<Map<String, dynamic>>>(
                  // Both organizationId and studentId are required by the
                  // tenant-isolation rules; an unscoped collection query is denied.
                  stream: FirebaseFirestore.instance
                      .collection('enrollments')
                      .where('organizationId', isEqualTo: currentOrganizationId)
                      .where('studentId', isEqualTo: user.uid)
                      .snapshots(),
                  builder: (context, enrollmentSnapshot) {
                    if (enrollmentSnapshot.hasError) {
                      return const Center(
                        child: Text('Unable to load this workspace’s enrollments.'),
                      );
                    }
                    if (!enrollmentSnapshot.hasData) {
                      return const Center(child: CircularProgressIndicator());
                    }
                    final docs = enrollmentSnapshot.data!.docs;
                    if (docs.isEmpty) {
                      return const Center(
                        child: Text('No enrollment records in this workspace yet.'),
                      );
                    }
                    return ListView.builder(
                      itemCount: docs.length,
                      itemBuilder: (context, index) {
                        final data = docs[index].data();
                        return Card(
                          margin: const EdgeInsets.symmetric(
                            horizontal: 16,
                            vertical: 6,
                          ),
                          child: ListTile(
                            leading: const Icon(Icons.menu_book),
                            title: Text(
                              data['batchId']?.toString() ?? 'Course batch',
                            ),
                            subtitle: Text(
                              'Status: ${data['status'] ?? 'pending'}',
                            ),
                            trailing: const Icon(Icons.chevron_right),
                          ),
                        );
                      },
                    );
                  },
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _signOutButton() => IconButton(
        tooltip: 'Sign out',
        onPressed: () => FirebaseAuth.instance.signOut(),
        icon: const Icon(Icons.logout),
      );

  Widget _messageScaffold(String message) => Scaffold(
        appBar: AppBar(
          title: const Text('My Learning'),
          actions: [_signOutButton()],
        ),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Text(message, textAlign: TextAlign.center),
          ),
        ),
      );
}
